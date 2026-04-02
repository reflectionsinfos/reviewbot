gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=reviewbot-web AND severity>=ERROR" --limit 10 --project reviewbot-491619 --format="value(textPayload)"
