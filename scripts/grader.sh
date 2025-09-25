#!/bin/bash
# Simple wrapper for autograder endpoints

BASE="http://dl-berlin.ecn.purdue.edu/api"
GROUP=2
REPO="https://github.com/ECE461ProjTeam/ModelReuseCLI"

# Read token from env var or a file
if [ -z "$GH_TOKEN" ]; then
  if [ -f git_token.txt ]; then
    GH_TOKEN=$(cat git_token.txt)
  else
    echo "  No GitHub token found. Set GH_TOKEN or put it in git_token.txt"
    exit 1
  fi
fi

case "$1" in
  register)
    curl --location "$BASE/register" \
      -H "Content-Type: application/json" \
      --data "{
        \"group\": $GROUP,
        \"github\": \"$REPO\",
        \"names\": [
          \"Murad Ibrahimov\",
          \"Vatsal Dudhaiya\",
          \"Mikhail Golovenchits\",
          \"Jacob Scherer\"
        ],
        \"gh_token\": \"$GH_TOKEN\"
      }"
    ;;
  schedule)
    curl --location "$BASE/schedule" \
      -H "Content-Type: application/json" \
      --data "{
        \"group\": $GROUP,
        \"gh_token\": \"$GH_TOKEN\"
      }"
    ;;
  last)
    curl --location --request GET "$BASE/last_run" \
      -H "Content-Type: application/json" \
      --data "{
        \"group\": $GROUP,
        \"gh_token\": \"$GH_TOKEN\"
      }"
    ;;
  best)
    curl --location --request GET "$BASE/best_run" \
      -H "Content-Type: application/json" \
      --data "{
        \"group\": $GROUP,
        \"gh_token\": \"$GH_TOKEN\"
      }"
    ;;
  monitor)
    curl --location --request GET "$BASE/run/all" \
      -H "Content-Type: application/json" \
      --data "{
        \"group\": $GROUP,
        \"gh_token\": \"$GH_TOKEN\"
      }"
    ;;
  *)
    echo "Usage: $0 {register|schedule|last|best|monitor}"

esac