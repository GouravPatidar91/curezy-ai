import argparse
from awq import AutoAWQForCausalLM
from transformers import AutoTokenizer

def quantize_model(model_path: str, quant_path: str):
    print(f"Quantizing {model_path} -> {quant_path}...")
    
    model = AutoAWQForCausalLM.from_pretrained(
        model_path, 
        **{"low_cpu_mem_usage": True, "use_cache": False}
    )
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

    quant_config = {
        "zero_point": True,
        "q_group_size": 128,
        "w_bit": 4,
        "version": "GEMM"
    }

    model.quantize(
        tokenizer, 
        quant_config=quant_config
    )

    model.save_quantized(quant_path)
    tokenizer.save_pretrained(quant_path)
    print(f"✅ Quantization complete: {quant_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, required=True, help="HF model ID or local path")
    parser.add_argument("--output", type=str, required=True, help="Output path for AWQ model")
    args = parser.parse_args()
    
    quantize_model(args.model, args.output)
