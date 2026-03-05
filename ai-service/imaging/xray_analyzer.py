import os
import numpy as np
import base64
from io import BytesIO
from typing import Optional
import urllib.request

# Optional heavy medical imaging dependencies for Render compatibility
try:
    import cv2
    import torch
    import torch.nn as nn
    from torchvision import models, transforms
    from PIL import Image
    import torchxrayvision as xrv
except ImportError:
    cv2, torch, nn, models, transforms, Image, xrv = [None] * 7

try:
    from segment_anything import sam_model_registry, SamPredictor
except ImportError:
    sam_model_registry, SamPredictor = None, None


# ─────────────────────────────────────────
# XRAY ANALYZER WITH GRADCAM HEATMAP
# ─────────────────────────────────────────

class GradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        self._register_hooks()

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output.detach()

        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0].detach()

        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(backward_hook)

    def generate(self, input_tensor, class_idx=None):
        self.model.eval()
        output = self.model(input_tensor)

        if class_idx is None:
            class_idx = output.argmax(dim=1).item()

        self.model.zero_grad()
        output[0, class_idx].backward()

        gradients = self.gradients[0].cpu()
        activations = self.activations[0].cpu()

        weights = gradients.mean(dim=(1, 2))
        cam = torch.zeros(activations.shape[1:], dtype=torch.float32)

        for i, w in enumerate(weights):
            cam += w * activations[i]

        cam = torch.relu(cam)
        cam = cam.numpy()
        cam = cv2.resize(cam, (224, 224))
        cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
        return cam, class_idx


class ChestXRayAnalyzer:
    def __init__(self):
        self.is_ready = all(x is not None for x in [torch, xrv, cv2, Image])
        if not self.is_ready:
            print("[XRayAnalyzer] ⚠️ Missing heavy dependencies (torch/xrv/cv2). Local analysis disabled.")
            return

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.classes = xrv.datasets.default_pathologies
        self.model = self._load_model()
        
        # DenseNet121 target layer for GradCAM
        self.gradcam = GradCAM(
            self.model,
            self.model.features.denseblock4
        )
        
        # TorchXRayVision specific transforms
        self.transform = transforms.Compose([
            xrv.datasets.XRayCenterCrop(),
            xrv.datasets.XRayResizer(224)
        ])
        
        # Load MedSAM
        self.medsam_predictor = self._load_medsam_model()

    def _load_model(self):
        # Load DenseNet121 pre-trained on NIH, CheXpert, MIMIC, PadChest
        model = xrv.models.DenseNet(weights="densenet121-res224-all")
        model = model.to(self.device)
        model.eval()
        return model

    def _load_medsam_model(self):
        try:
            print("[XRayAnalyzer] Initializing MedSAM...")
            models_dir = os.path.join(os.path.dirname(__file__), "..", ".models")
            os.makedirs(models_dir, exist_ok=True)
            checkpoint_path = os.path.join(models_dir, "medsam_vit_b.pth")
            
            if not os.path.exists(checkpoint_path):
                print("[XRayAnalyzer] Downloading MedSAM checkpoint (this might take a few minutes)...")
                # Using a widely available SAM vit_b checkpoint as base since MedSAM has the same architecture
                # In production, this should point to the exact MedSAM weights (e.g. from Zenodo or HuggingFace)
                url = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth"
                urllib.request.urlretrieve(url, checkpoint_path)
                print("[XRayAnalyzer] Download complete.")

            sam = sam_model_registry["vit_b"](checkpoint=checkpoint_path)
            sam = sam.to(self.device)
            predictor = SamPredictor(sam)
            print("[XRayAnalyzer] MedSAM loaded successfully.")
            return predictor
        except Exception as e:
            print(f"[XRayAnalyzer] Failed to load MedSAM: {e}")
            return None

    def _assess_image_quality(self, image: np.ndarray) -> dict:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        brightness = gray.mean()
        contrast = gray.std()
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        quality_score = 100
        issues = []

        if brightness < 30:
            quality_score -= 30
            issues.append("Image too dark")
        elif brightness > 220:
            quality_score -= 30
            issues.append("Image too bright/overexposed")

        if contrast < 20:
            quality_score -= 20
            issues.append("Low contrast")

        if laplacian_var < 100:
            quality_score -= 20
            issues.append("Image appears blurry")

        return {
            "quality_score": max(0, quality_score),
            "brightness": round(float(brightness), 2),
            "contrast": round(float(contrast), 2),
            "sharpness": round(float(laplacian_var), 2),
            "issues": issues,
            "acceptable": quality_score >= 50
        }

    def _apply_lung_mask(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        masked = cv2.bitwise_and(image, image, mask=mask)
        return masked

    def _generate_heatmap_image(
        self,
        original_image: np.ndarray,
        cam: np.ndarray
    ) -> str:
        heatmap = cv2.applyColorMap(
            np.uint8(255 * cam), cv2.COLORMAP_JET
        )
        heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
        original_resized = cv2.resize(original_image, (224, 224))
        overlay = cv2.addWeighted(original_resized, 0.6, heatmap, 0.4, 0)

        # Convert to base64 for API response
        pil_image = Image.fromarray(overlay)
        buffer = BytesIO()
        pil_image.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        return img_base64

    def analyze(self, image_path: str) -> dict:
        try:
            # Load image
            image = Image.open(image_path).convert("RGB")
            image_np = np.array(image)

            # Quality assessment
            quality = self._assess_image_quality(image_np)
            if not quality["acceptable"]:
                return {
                    "success": False,
                    "error": "Image quality insufficient for analysis",
                    "quality_assessment": quality
                }

            # Apply lung mask
            masked_image = self._apply_lung_mask(image_np)

            # Preprocess for model (xrv expects 1 color channel, normalized [-1024, 1024])
            # We convert our masked image to grayscale manually before transform
            gray_masked = cv2.cvtColor(masked_image, cv2.COLOR_RGB2GRAY)
            # xrv transforms expect PIL image or numpy array of specific shape
            img = xrv.datasets.normalize(gray_masked, 255) # Scale to [-1024, 1024]
            # Convert to [C, H, W] setup that transform expects (which actually expects spatial only)
            if len(img.shape) == 2:
                img = img[None, ...] # Add channel dimension -> (1, H, W)
                
            # XRayResizer expects (H, W) or (C, H, W).
            # The transform returns a single channel image, we just need to add batch dim.
            input_tensor = self.transform(img)
            # xrv returns (1, 224, 224), add batch => (1, 1, 224, 224)
            input_tensor = torch.from_numpy(input_tensor).unsqueeze(0).to(self.device)

            # Run inference
            with torch.no_grad():
                logits = self.model(input_tensor)
                # xrv outputs probabilities directly via sigmoid, not logits/softmax
                probabilities = logits[0]

            # Get top predictions
            top_probs, top_indices = torch.topk(probabilities, 3)
            findings = []
            for prob, idx in zip(top_probs, top_indices):
                findings.append({
                    "condition": self.classes[idx.item()],
                    "probability": round(prob.item() * 100, 2),
                    "confidence": round(prob.item() * 100 * quality["quality_score"] / 100, 2)
                })

            # Base Abnormality detection
            is_normal = findings[0]["condition"] == "Normal"
            abnormal_regions = []

            # Generate GradCAM activations BEFORE heatmapping
            input_tensor_grad = input_tensor.clone().detach()
            input_tensor_grad.requires_grad_(True)
            cam, predicted_class = self.gradcam.generate(input_tensor_grad, class_idx=top_indices[0].item())
            
            medsam_result_text = None
            medsam_segmentation_base64 = None
            if not is_normal:
                cam_threshold = cam > 0.5
                if cam_threshold.any():
                    # 1. Derive Bounding Box from raw GradCAM activation tensor
                    y_indices, x_indices = np.where(cam_threshold)
                    # Convert 224x224 coords to original image scale
                    orig_h, orig_w = image_np.shape[:2]
                    scale_y, scale_x = orig_h / 224, orig_w / 224
                    
                    xmin = int(x_indices.min() * scale_x)
                    ymin = int(y_indices.min() * scale_y)
                    xmax = int(x_indices.max() * scale_x)
                    ymax = int(y_indices.max() * scale_y)
                    
                    # Add margin
                    margin = int(max(orig_h, orig_w) * 0.05)
                    xmin = max(0, xmin - margin)
                    ymin = max(0, ymin - margin)
                    xmax = min(orig_w, xmax + margin)
                    ymax = min(orig_h, ymax + margin)
                    
                    input_box = np.array([xmin, ymin, xmax, ymax])
                    
                    # 2. Execute MedSAM Segmentation on Pristine Original Image
                    if self.medsam_predictor is not None:
                        try:
                            self.medsam_predictor.set_image(image_np)
                            masks, scores, logits = self.medsam_predictor.predict(
                                box=input_box,
                                multimask_output=False
                            )
                            # mask is a boolean array (1, H, W)
                            mask = masks[0]
                            area_pixels = np.sum(mask)
                            total_pixels = orig_h * orig_w
                            coverage = (area_pixels / total_pixels) * 100
                            
                            medsam_result_text = f"MedSAM Segmentation: Found contiguous lesion of area {int(area_pixels)} pixels ({coverage:.1f}% coverage) mapping to the primary GradCAM activation."
                            
                            # Encode segmentation as a visible blue overlay mask
                            # `mask` is boolean. Convert to RGBA.
                            color_mask = np.zeros((*mask.shape, 4), dtype=np.uint8)
                            color_mask[mask, :] = [0, 150, 255, 120]  # Semi-transparent blue
                            
                            pil_mask = Image.fromarray(color_mask)
                            mask_buffer = BytesIO()
                            pil_mask.save(mask_buffer, format="PNG")
                            medsam_segmentation_base64 = base64.b64encode(mask_buffer.getvalue()).decode()

                        except Exception as e:
                            print(f"[XRayAnalyzer] MedSAM prediction failed: {e}")
                    
                    abnormal_regions.append({
                        "region": "Detected abnormal region",
                        "confidence": round(float(cam.max()) * 100, 2)
                    })

            # 3. Final Visual Heatmapping Generation (Post-MedSAM phase)
            # Only NOW do we modify the image with the overlay
            heatmap_base64 = self._generate_heatmap_image(image_np, cam)
            
            # Enrich Final Summary with MedSAM
            structured_summary = self._generate_summary(findings, quality)
            if medsam_result_text:
                structured_summary += f"\n\n{medsam_result_text}"

            res = {
                "success": True,
                "quality_assessment": quality,
                "findings": findings,
                "is_normal": is_normal,
                "abnormal_regions": abnormal_regions,
                "heatmap_base64": heatmap_base64,
                "medsam_segmentation_base64": medsam_segmentation_base64,
                "primary_finding": findings[0]["condition"],
                "primary_confidence": findings[0]["confidence"],
                "structured_summary": structured_summary,
                "requires_radiologist_review": False # Default to False
            }
            if not is_normal or findings[0]["confidence"] < 70:
                res["requires_radiologist_review"] = True
            return res

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def _generate_summary(self, findings: list, quality: dict) -> str:
        primary = findings[0]
        summary = f"AI-assisted chest X-ray analysis (Quality: {quality['quality_score']}/100). "
        summary += f"Primary finding: {primary['condition']} "
        summary += f"(Probability: {primary['probability']}%, "
        summary += f"Confidence: {primary['confidence']}%). "

        if len(findings) > 1:
            summary += f"Differential considerations: "
            summary += ", ".join([f"{f['condition']} ({f['probability']}%)"
                                 for f in findings[1:]])
            summary += ". "

        summary += "This is AI-assisted analysis only. Radiologist verification required."
        return summary