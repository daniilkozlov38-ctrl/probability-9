"""Compatibility entry point: the .tex lesson is the only content source."""
import runpy
from pathlib import Path
def main():
    runpy.run_path(str(Path(__file__).with_name("build-tex-lesson.py")),run_name="__main__")
if __name__=="__main__": main()
