import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from ml.video.faceforensics import FaceForensicsDetector
from ml.video.syncsnet import SyncNetDetector
import structlog

logger = structlog.get_logger()

async def diagnose():
    print("--- Veridian Forensic Diagnostic ---")
    
    print("\n[1/2] Checking FaceForensics (Deepfake)...")
    ff = FaceForensicsDetector()
    if ff.uncalibrated:
        print("FAIL - FaceForensics: Still UNCALIBRATED")
    else:
        print("SUCCESS - FaceForensics: LIVE")
        
    print("\n[2/2] Checking SyncNet (Lip-Sync)...")
    sn = SyncNetDetector()
    if sn.uncalibrated:
        print("FAIL - SyncNet: Still UNCALIBRATED")
    else:
        print("SUCCESS - SyncNet: LIVE")

if __name__ == "__main__":
    import asyncio
    asyncio.run(diagnose())
