from flask import Flask, render_template_string, jsonify
from datetime import datetime, timedelta
import json

app = Flask(__name__)

# Mock job data
MOCK_JOBS = [
    {
        "id": "job_1",
        "title": "Senior Python Developer",
        "company": "TechCorp",
        "location": "San Francisco, CA",
        "description": "We're looking for an experienced Python developer to join our backend team. Work with FastAPI, PostgreSQL, and AWS.",
        "url": "https://techcorp.com/jobs/1",
        "job_type": "Full-time",
        "published_at": (datetime.now() - timedelta(days=1)).isoformat(),
    },
    {
        "id": "job_2",
        "title": "Full Stack Developer",
        "company": "StartupXYZ",
        "location": "New York, NY",
        "description": "Join our growing startup! Build features with React and Node.js. We value ownership and impact.",
        "url": "https://startupxyz.com/jobs/2",
        "job_type": "Full-time",
        "published_at": (datetime.now() - timedelta(days=2)).isoformat(),
    },
    {
        "id": "job_3",
        "title": "DevOps Engineer",
        "company": "CloudInc",
        "location": "Remote",
        "description": "Manage our Kubernetes infrastructure. Experience with Docker, CI/CD, and cloud platforms required.",
        "url": "https://cloudinc.com/jobs/3",
        "job_type": "Full-time",
        "published_at": (datetime.now() - timedelta(days=3)).isoformat(),
    },
    {
        "id": "job_4",
        "title": "Data Scientist",
        "company": "AI Solutions",
        "location": "Boston, MA",
        "description": "Build ML models for our customers. Python, TensorFlow, and SQL expertise needed.",
        "url": "https://aisolutions.com/jobs/4",
        "job_type": "Full-time",
        "published_at": (datetime.now() - timedelta(days=4)).isoformat(),
    },
    {
        "id": "job_5",
        "title": "Frontend Engineer",
        "company": "DesignStudio",
        "location": "Los Angeles, CA",
        "description": "Create beautiful UIs with React and TypeScript. You'll work with our design team closely.",
        "url": "https://designstudio.com/jobs/5",
        "job_type": "Full-time",
        "published_at": (datetime.now() - timedelta(days=5)).isoformat(),
    },
]


@app.route("/")
def index():
    """Sandbox homepage."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>JobPulse Sandbox - Test Job Listings</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .job { border: 1px solid #ccc; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .job h2 { margin: 0 0 10px 0; }
            .company { color: #666; font-weight: bold; }
            .location { color: #999; }
            .description { margin: 10px 0; }
            a { color: #0066cc; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <h1>JobPulse Sandbox - Test Job Listings</h1>
        <p>This is a controlled job listing website for testing ingestion.</p>
        <p><a href="/api/jobs">View JSON API</a> | <a href="/health">Health Check</a></p>
        <hr>
    """
    
    for job in MOCK_JOBS:
        html += f"""
        <div class="job" data-job-id="{job['id']}">
            <h2>{job['title']}</h2>
            <div class="company">{job['company']}</div>
            <div class="location">{job['location']}</div>
            <div class="description">{job['description']}</div>
            <a href="{job['url']}" target="_blank">View Job</a>
        </div>
        """
    
    html += """
    </body>
    </html>
    """
    return html


@app.route("/api/jobs")
def api_jobs():
    """Return jobs as JSON API."""
    return jsonify({"jobs": MOCK_JOBS})


@app.route("/api/jobs/<job_id>")
def api_job(job_id):
    """Return single job."""
    for job in MOCK_JOBS:
        if job["id"] == job_id:
            return jsonify(job)
    return jsonify({"error": "Job not found"}), 404


@app.route("/health")
def health():
    """Health check."""
    return jsonify({
        "status": "healthy",
        "jobs_available": len(MOCK_JOBS),
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
