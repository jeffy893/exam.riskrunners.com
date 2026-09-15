#!/bin/bash
# Double-click this file (Finder) to generate ONE new P (Probability) practice exam.
# It runs the Python pipeline, which persists the exam into data/ and keeps a
# rolling maximum of 10 P exams (oldest is expunged when an 11th is made).
#
# After it finishes, review the site locally, then push to main:
#     git add -A && git commit -m "Add P practice exam" && git push
cd "$(dirname "$0")" || exit 1
echo "=============================================="
echo "  Risk Runners — Generate P Practice Exam"
echo "=============================================="
python3 generator/generate_exam.py P
STATUS=$?
echo ""
if [ $STATUS -eq 0 ]; then
  echo "P exam generated. Push to main when ready."
else
  echo "Generation failed (exit $STATUS). See messages above."
fi
echo ""
read -n 1 -s -r -p "Press any key to close this window..."
echo ""
