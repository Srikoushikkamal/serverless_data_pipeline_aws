STACK ?= olist-pipeline
BUCKET = $(shell aws cloudformation describe-stacks --stack-name $(STACK) \
	--query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" --output text)

.PHONY: install lint test check deploy upload-script run

install:
	pip install -r requirements-dev.txt

lint:
	ruff check .
	cfn-lint template.yaml

test:
	python -m pytest

check: lint test

# Needs the AWS SAM CLI and AWS credentials on your machine.
deploy:
	sam build
	sam deploy --stack-name $(STACK) --capabilities CAPABILITY_IAM --resolve-s3 --parameter-overrides ProjectName=$(STACK)

# The Glue job reads its script from the bucket the stack created.
upload-script:
	aws s3 cp glue/incoming_to_processed.py s3://$(BUCKET)/scripts/incoming_to_processed.py

# Start the job by hand, without waiting for a file to arrive.
run:
	aws glue start-job-run --job-name $(STACK)-incoming-to-processed
