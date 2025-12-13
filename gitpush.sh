#!/bin/bash
COMMIT_MESSAGE="Quick update"

# Check if a custom message is provided as argument
if [ ! -z "$1" ]; then
  COMMIT_MESSAGE="$1"
fi

git add .
echo $?
git commit -m "$COMMIT_MESSAGE"
echo $?
git push -u origin mai
echo $?

echo "Changes committed with message: '$COMMIT_MESSAGE' and pushed successfully!"
