#!/bin/bash
for fn in $(gcloud functions list --format="value(name)"); do
  echo "Allowing unauthenticated access to function: $fn"
  gcloud functions add-iam-policy-binding "$fn" \
    --region=us-central1 \
    --member="allUsers" \
    --role="roles/cloudfunctions.invoker"
done

