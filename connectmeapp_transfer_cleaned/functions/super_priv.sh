for fn in $(gcloud functions list --region=us-central1 --format="value(name)"); do
  echo "Deleting function: $fn"
  gcloud functions delete "$fn" --region=us-central1 --quiet
done
