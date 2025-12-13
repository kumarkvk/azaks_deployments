#!/bin/bash
read -p "Enter commit message: " COMMIT_MESSAGE

# Check if a custom message is provided as argument
if [ -z "$COMMIT_MESSAGE" ]; then
  COMMIT_MESSAGE="Update $(date '+%Y-%m-%d %H:%M:%S')"
fi

git add .
echo $?
git commit -m "$COMMIT_MESSAGE"
echo $?
git push -u origin main
echo $?

echo "Changes committed with message: '$COMMIT_MESSAGE' and pushed successfully!"
