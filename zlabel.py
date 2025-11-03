# -*- coding: utf-8 -*-

import sys

from zlabel.main import main

if sys.stdout is None:
    sys.stdout = open(f"{__file__}.out.txt", "w")
if sys.stderr is None:
    sys.stderr = open(f"{__file__}.err.txt", "w")

if __name__ == "__main__":
    main()
