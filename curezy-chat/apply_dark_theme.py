import os

replacements = {
    # Text colors
    "text-slate-800": "text-white",
    "text-gray-900": "text-white",
    "text-slate-900": "text-white",
    "text-gray-800": "text-white",
    "text-slate-700": "text-gray-200",
    "text-gray-700": "text-gray-200",
    "text-slate-500": "text-gray-400",
    "text-gray-500": "text-gray-400",
    "text-slate-400": "text-gray-500",
    "text-gray-400": "text-gray-500",
    
    # Backgrounds
    "bg-white ": "bg-surface ",
    "bg-white\"": "bg-surface\"",
    "bg-white}": "bg-surface}",
    "bg-white/40": "bg-surface/50",
    "bg-white/50": "bg-surface-light",
    "bg-white/60": "bg-surface-light",
    "bg-white/80": "bg-surface-light",
    "bg-gray-50": "bg-white/5",
    "bg-gray-100": "bg-white/10",
    "bg-gray-200": "bg-white/20",
    
    # Borders
    "border-white/20": "border-white/10",
    "border-white/30": "border-white/10",
    "border-white/40": "border-white/10",
    "border-white/50": "border-white/10",
    "border-white/60": "border-white/10",
    "border-gray-100": "border-white/10",
    "border-gray-200": "border-white/10",
    
    # Primary colors
    "bg-primary-50 ": "bg-accent-blue/10 ",
    "bg-primary-100/50": "bg-accent-purple/20",
    "border-primary-200": "border-accent-purple/20",
    "bg-primary-100": "bg-accent-blue/20",
    "bg-primary-200": "bg-accent-blue/30",
    "bg-primary-400": "bg-accent-blue/60",
    "bg-primary-500": "bg-accent-blue",
    "bg-primary-600": "bg-accent-purple",
    "bg-primary-700": "bg-accent-purple/80",
    "text-primary-100": "text-gray-300",
    "text-primary-500": "text-accent-blue",
    "text-primary-600": "text-accent-blue",
    "text-primary-700": "text-accent-blue",
    "text-primary-800": "text-accent-purple",
    "border-primary-400": "border-accent-blue",
    "ring-primary-400": "ring-accent-blue",
    "ring-primary-100": "ring-accent-blue/20",
    "shadow-primary-500/20": "shadow-[0_0_15px_rgba(123,44,191,0.3)]",
    
    # Base elements
    "bg-slate-900": "bg-accent-blue",
    "hover:bg-primary-600": "hover:bg-accent-purple",
    "hover:bg-primary-500": "hover:bg-accent-purple/80",
    "active:bg-primary-700": "active:bg-accent-purple",
    
    # Badges mapping
    "bg-indigo-100 text-indigo-700": "bg-indigo-500/20 text-indigo-300",
    "bg-yellow-100 text-yellow-700": "bg-yellow-500/20 text-yellow-300",
    "bg-orange-100 text-orange-700": "bg-orange-500/20 text-orange-300",
    "bg-amber-100 text-amber-700": "bg-amber-500/20 text-amber-300",
    "bg-purple-100 text-purple-700": "bg-purple-500/20 text-purple-300",
    "bg-blue-100 text-blue-700": "bg-blue-500/20 text-blue-300",
    "bg-teal-100 text-teal-700": "bg-teal-500/20 text-teal-300",
    "bg-cyan-100 text-cyan-700": "bg-cyan-500/20 text-cyan-300",
    "bg-emerald-100 text-emerald-700": "bg-emerald-500/20 text-emerald-300",
    "bg-green-100 text-green-700": "bg-green-500/20 text-green-300",
    "bg-red-50 text-red-600": "bg-red-500/20 text-red-300",
    "bg-green-50 text-green-700": "bg-green-500/20 text-green-300",
}

files = [
    "src/pages/Chat.jsx",
    "src/components/Sidebar.jsx",
    "src/components/MessageBubble.jsx"
]

base_dir = r"e:\Curezy-ai\curezy-chat"

for file_path in files:
    full_path = os.path.join(base_dir, file_path)
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        for old, new in replacements.items():
            content = content.replace(old, new)
            
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {file_path}")
