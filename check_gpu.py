#!/usr/bin/env python3
"""
GPU Environment Check Script

Check available GPU environment for FuguMT Translation Server.
"""

import sys
import platform


def check_python_environment():
    """Check Python environment"""
    print("Python Environment:")
    print(f"   Version: {sys.version}")
    print(f"   Platform: {platform.platform()}")
    print()


def check_pytorch():
    """Check PyTorch environment"""
    print("PyTorch Environment:")
    
    try:
        import torch
        print(f"   PyTorch: {torch.__version__}")
        print(f"   CUDA Available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"   CUDA Version: {torch.version.cuda}")
            gpu_count = torch.cuda.device_count()
            print(f"   GPU Devices: {gpu_count}")
            print()
            print("   Available GPUs:")
            
            for i in range(gpu_count):
                gpu_name = torch.cuda.get_device_name(i)
                gpu_properties = torch.cuda.get_device_properties(i)
                gpu_memory = gpu_properties.total_memory / (1024**3)
                compute_capability = f"{gpu_properties.major}.{gpu_properties.minor}"
                
                # Memory usage if possible
                try:
                    torch.cuda.empty_cache()
                    allocated = torch.cuda.memory_allocated(i) / (1024**3)
                    cached = torch.cuda.memory_reserved(i) / (1024**3)
                    free = gpu_memory - cached
                    print(f"   GPU {i}: {gpu_name}")
                    print(f"      Memory: {gpu_memory:.1f}GB (Used: {cached:.1f}GB, Free: {free:.1f}GB)")
                    print(f"      Compute Capability: {compute_capability}")
                    print(f"      Config: device = cuda, gpu_id = {i}")
                except Exception:
                    print(f"   GPU {i}: {gpu_name}")
                    print(f"      Memory: {gpu_memory:.1f}GB")
                    print(f"      Compute Capability: {compute_capability}")
                    print(f"      Config: device = cuda, gpu_id = {i}")
                print()
            
            if gpu_count > 1:
                print("   Multiple GPUs detected!")
                print("   You can specify GPU ID in config file:")
                print("   In config/fugumt_translator.ini [TRANSLATION] section:")
                print("   device = cuda")
                print("   gpu_id = 0  # GPU ID to use (0-based)")
                print()
        else:
            print("   CUDA not available - using CPU mode")
            print("   For CPU usage, set: device = cpu")
        
        # Apple Silicon (MPS) check
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            print("   MPS (Apple Silicon): Available")
        
        print()
        
    except ImportError:
        print("   [ERROR] PyTorch not installed")
        print("      Install with: pip install torch")
        print()


def check_transformers():
    """Check Transformers environment"""
    print("Transformers Environment:")
    
    try:
        import transformers
        print(f"   Transformers: {transformers.__version__}")
        print()
    except ImportError:
        print("   [ERROR] Transformers not installed")
        print("      Install with: pip install transformers")
        print()


def check_websockets():
    """Check WebSockets environment"""
    print("WebSockets Environment:")
    
    try:
        import websockets
        print(f"   WebSockets: {websockets.__version__}")
        print()
    except ImportError:
        print("   [ERROR] WebSockets not installed")
        print("      Install with: pip install websockets")
        print()


def check_fugumt_model():
    """Check FuguMT model access"""
    print("FuguMT Model Access Test:")
    
    try:
        from transformers import MarianTokenizer, MarianMTModel
        
        model_name = "staka/fugumt-en-ja"
        print(f"   Model: {model_name}")
        
        # Tokenizer test
        print("   Loading tokenizer...")
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        print("   [SUCCESS] Tokenizer loaded")
        
        # Model test (uses significant memory)
        print("   Loading model...")
        model = MarianMTModel.from_pretrained(model_name)
        print("   [SUCCESS] Model loaded")
        
        # Simple translation test
        print("   Running translation test...")
        inputs = tokenizer("Hello world", return_tensors="pt")
        outputs = model.generate(**inputs, max_length=50, num_beams=4)
        translated = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"   Test translation: 'Hello world' -> '{translated}'")
        print("   [SUCCESS] Translation test completed")
        print()
        
    except Exception as e:
        print(f"   [ERROR] {e}")
        print("   Network connection or model download issue")
        print()


def check_system_resources():
    """Check system resources"""
    print("System Resources:")
    
    try:
        import psutil
        
        # CPU information
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"   CPU: {cpu_count} cores (Usage: {cpu_percent}%)")
        
        # Memory information
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        memory_percent = memory.percent
        print(f"   Memory: {memory_gb:.1f}GB (Usage: {memory_percent}%)")
        
        if memory_gb < 4:
            print("   [WARNING] Memory < 4GB. Performance may be limited.")
        elif memory_gb < 8:
            print("   [WARNING] Memory < 8GB. Large models may have issues.")
        
        # Disk space
        disk = psutil.disk_usage('.')
        disk_gb = disk.free / (1024**3)
        print(f"   Available disk space: {disk_gb:.1f}GB")
        
        if disk_gb < 5:
            print("   [WARNING] Low disk space. Required for model downloads.")
        
        print()
        
    except ImportError:
        print("   psutil not installed (optional)")
        print("   Install with: pip install psutil for detailed info")
        print()


def run_comprehensive_test():
    """Run comprehensive test"""
    print("Comprehensive Operation Test:")
    
    try:
        # Import test for FuguMTTranslator
        from FuguMTTranslator import Config, FuguMTTranslator
        
        print("   Creating configuration...")
        config = Config()
        print("   [SUCCESS] Configuration created")
        
        print("   Initializing translation engine...")
        # Note: This takes time and uses significant memory
        print("   (This process may take some time...)")
        
        # Force CPU mode to avoid CUDA errors
        import torch
        if not torch.cuda.is_available():
            config.device = 'cpu'
            print("   [INFO] CUDA not available, using CPU mode")
        
        translator = FuguMTTranslator(config)
        print("   [SUCCESS] Translation engine initialized")
        
        print("   Running health check...")
        health = translator.health_check()
        print(f"   Health status: {health['status']}")
        print(f"   Device in use: {health['device']}")
        
        # GPU details if using CUDA
        if health['device'].startswith('cuda') and torch.cuda.is_available():
            if ':' in health['device']:
                gpu_id = int(health['device'].split(':')[1])
            else:
                gpu_id = torch.cuda.current_device()
            
            gpu_name = torch.cuda.get_device_name(gpu_id)
            gpu_memory = torch.cuda.get_device_properties(gpu_id).total_memory / (1024**3)
            try:
                allocated = torch.cuda.memory_allocated(gpu_id) / (1024**3)
                print(f"   GPU details: {gpu_name} (ID: {gpu_id})")
                print(f"   GPU memory: {gpu_memory:.1f}GB (Currently used: {allocated:.1f}GB)")
            except Exception:
                print(f"   GPU details: {gpu_name} (ID: {gpu_id}, Memory: {gpu_memory:.1f}GB)")
        
        print("   [SUCCESS] Comprehensive test completed")
        print()
        
    except Exception as e:
        print(f"   [ERROR] Comprehensive test failed: {e}")
        print("   Run setup.py to complete the setup")
        print()


def main():
    """Main process"""
    print("="*50)
    print("FuguMT Translation Server Environment Check")
    print("="*50)
    print()
    
    # Basic environment checks
    check_python_environment()
    check_pytorch()
    check_transformers()
    check_websockets()
    
    # System resource check
    check_system_resources()
    
    # FuguMT model check
    check_fugumt_model()
    
    # Comprehensive test
    run_comprehensive_test()
    
    print("="*50)
    print("Environment Check Completed")
    print("="*50)
    print()
    print("Recommendations:")
    print("- Ensure sufficient memory (8GB+) for GPU usage")
    print("- First run may take time for model downloads")
    print("- Stable network connection required")


if __name__ == "__main__":
    main()