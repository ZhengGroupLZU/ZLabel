import sys

from zlabel.main import main

if getattr(sys, "frozen", False):
    sys.stdout = open("ZLabel.out.txt", "w")
    sys.stderr = open("ZLabel.err.txt", "w")

if __name__ == "__main__":
    main()
