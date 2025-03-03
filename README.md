# ecfr-analyzer
![Project Architecture] (eCFR.png)

## Overview
This project is a serverless solution to analyze Federal Regulations (eCFR) using AWS. It downloads data from the public eCFR API, performs custom analyses (such as word counts per agency and historical trend analysis), and then makes the results available for visualization.

### Architecture
**Backend**
	•	AWS Lambda (Python):
A Lambda function (deployed via AWS SAM) fetches data from various eCFR API endpoints based on an action parameter (e.g., refresh, full_refresh, or detailed), performs custom analysis, and writes results:
	•	Raw Data: Stored in an S3 bucket.
	•	Summary Metrics: Stored in a DynamoDB table.
	•	API Gateway:
Provides HTTP endpoints (with CORS support) that trigger the Lambda function.
	•	IAM & Environment:
The SAM template sets up inline IAM policies and passes configuration via environment variables (S3 bucket and DynamoDB table names).

**Frontend**
	•	Vite (React):
A lightweight, modern React application provides a user interface with multiple buttons for triggering different data refresh actions (e.g., “Refresh Agencies,” “Full Refresh,” and “Detailed Analysis”).
	•	Static Website Hosting on S3:
The production build is deployed to an S3 bucket configured for static website hosting.

**Data Analytics & Visualization**
	•	AWS Glue & Athena:
A Glue crawler catalogs the DynamoDB (or S3) data, making it queryable by Athena.
	•	Amazon QuickSight:
QuickSight is used to build interactive dashboards from the Athena queries, allowing you to visualize trends and metrics over time.

#### How It Works
	1.	Data Ingestion & Analysis:
	•	The Lambda function makes API calls to one or more eCFR endpoints (with support for pagination if needed).
	•	It performs analysis (e.g., counting agencies, computing custom metrics) and logs detailed processing steps.
	•	Raw JSON results are stored in S3, while summary metrics are written to DynamoDB.
	2.	User Interaction:
	•	The Vite React frontend provides buttons for users to trigger various actions (each mapped to different API calls).
	•	Users can view immediate API responses or later explore detailed analytics via QuickSight dashboards.
	3.	Reporting & Visualization:
	•	AWS Glue crawls the DynamoDB (or S3) data and makes it queryable in Athena.
	•	QuickSight connects to Athena to visualize the historical trends and custom metrics from the eCFR data.

**Deployment**
	•	Backend Deployment:
Use AWS SAM to build and deploy the Lambda function, API Gateway, S3 bucket, and DynamoDB table.

cd backend
sam build --use-container
sam deploy --guided


	•	Frontend Deployment:
Create a Vite React project, build the production version, and deploy the contents of the dist folder to an S3 bucket configured for static website hosting.

cd frontend
npm install
npm run build

Then, use the AWS Console or CLI to upload the dist contents to your hosting bucket.

	•	Analytics Setup:
Configure an AWS Glue crawler to catalog your DynamoDB (or S3) data, then use Athena to run queries and connect QuickSight for dashboards.

This solution leverages multiple AWS services to provide a fully integrated pipeline for fetching, analyzing, storing, and visualizing data from the eCFR API—all built using Python for the backend and Vite/React for the frontend.
