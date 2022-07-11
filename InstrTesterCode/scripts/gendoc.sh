#!/bin/bash
echo "Generating Documentation. . . "
pandoc ./wiki/Home.md -s --template=./resources/template.tex --latex-engine=xelatex --toc -o Instr-Tester.pdf
echo "Done."
