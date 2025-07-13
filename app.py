from flask import Flask, render_template, request, jsonify
from github import Github
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

# Get GitHub token from environment variable
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def check_token():
    if not GITHUB_TOKEN or GITHUB_TOKEN.strip() == "" or GITHUB_TOKEN == "your_github_token_here":
        raise RuntimeError("GitHub token is missing or invalid. Please set GITHUB_TOKEN in your .env file.")

# Check token at startup
check_token()

def analyze_github_profile(username):
    try:
        # Initialize Github instance
        g = Github(GITHUB_TOKEN)
        
        # Get the user
        try:
            user = g.get_user(username)
        except Exception as e:
            return None, f"GitHub user '{username}' not found or API error: {e}"
        
        # Get repositories
        repos = user.get_repos()
        
        # Analysis data
        analysis = {
            'name': user.name or username,
            'bio': user.bio,
            'location': user.location,
            'public_repos': user.public_repos,
            'followers': user.followers,
            'total_stars': 0,
            'languages': {},
            'top_repos': [],
            # 'contributions': user.contributions,  # Removed: not available in PyGithub
            'email': user.email,
            'company': user.company,
            'blog': user.blog,
            'avatar_url': user.avatar_url
        }
        
        # Analyze repositories
        for repo in repos:
            # Count stars
            analysis['total_stars'] += repo.stargazers_count
            
            # Count languages
            if repo.language:
                if repo.language in analysis['languages']:
                    analysis['languages'][repo.language] += 1
                else:
                    analysis['languages'][repo.language] = 1
            
            # Add to top repos if it has stars
            if repo.stargazers_count > 0:
                analysis['top_repos'].append({
                    'name': repo.name,
                    'description': repo.description,
                    'stars': repo.stargazers_count,
                    'language': repo.language,
                    'url': repo.html_url
                })
        
        # Sort top repos by stars
        analysis['top_repos'] = sorted(
            analysis['top_repos'], 
            key=lambda x: x['stars'], 
            reverse=True
        )[:5]  # Get top 5 repos
        
        # Sort languages by usage
        analysis['languages'] = dict(
            sorted(
                analysis['languages'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )
        )
        
        return analysis, None
    
    except Exception as e:
        if '401' in str(e) or 'Bad credentials' in str(e):
            return None, "GitHub API authentication failed. Please check your token."
        return None, str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    username = request.form.get('username')
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    analysis, error = analyze_github_profile(username)
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify(analysis)

if __name__ == '__main__':
    app.run(debug=True)
