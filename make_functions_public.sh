#!/bin/bash
# Makes all Cloud Functions publicly accessible (required for 2nd gen functions)
# The app handles authentication at the application level via @uauth

PROJECT="connectme-bef05"
REGION="us-central1"

FUNCTIONS=$(gcloud functions list --project=$PROJECT --region=$REGION --format="value(name)" 2>/dev/null)

for fn in $FUNCTIONS; do
  echo "Making $fn public..."
  gcloud functions add-invoker-policy-binding $fn \
    --region=$REGION \
    --member="allUsers" \
    --project=$PROJECT \
    --gen2 \
    --quiet 2>/dev/null
done

echo "Done!"
