import click
import requests
import json
import os

API_BASE_URL = "https://www.moltbook.com/api/v1"
CONFIG_DIR = os.path.expanduser("~/.config/moltbook")
CREDENTIALS_FILE = os.path.join(CONFIG_DIR, "credentials.json")

def save_credentials(api_key, agent_name):
    """Saves API key and agent name to the credentials file."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump({"api_key": api_key, "agent_name": agent_name}, f, indent=2)
    click.echo(f"Credentials saved to {CREDENTIALS_FILE}")

def load_credentials():
    """Loads credentials from the credentials file."""
    try:
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None

def get_api_key():
    """Gets the API key from credentials file or environment variable."""
    creds = load_credentials()
    if creds and "api_key" in creds:
        return creds["api_key"]
    return os.environ.get("MOLTBOOK_API_KEY")

@click.group()
def cli():
    """A CLI for interacting with the Moltbook API."""
    pass

@cli.command()
@click.option('--name', prompt="Your agent's name", help="The name of your agent.")
@click.option('--description', prompt="A short description of your agent", help="A description of what your agent does.")
def register(name, description):
    """Register a new agent with Moltbook."""
    url = f"{API_BASE_URL}/agents/register"
    payload = {"name": name, "description": description}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        click.echo("🎉 Registration successful!")
        click.echo(json.dumps(data, indent=2))

        api_key = data.get("agent", {}).get("api_key")
        if api_key:
            if click.confirm(f"Do you want to save the API key for agent '{name}'?"):
                save_credentials(api_key, name)
        else:
            click.echo("⚠️ Could not find API key in response.")

    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@cli.command()
def status():
    """Check the claim status of your agent."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    url = f"{API_BASE_URL}/agents/status"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        click.echo(json.dumps(response.json(), indent=2))
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@cli.command()
def me():
    """Get your agent's profile."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    url = f"{API_BASE_URL}/agents/me"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        click.echo(json.dumps(response.json(), indent=2))
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@click.group()
def posts():
    """Commands for interacting with posts."""
    pass

@posts.command()
@click.option('--submolt', default='general', help='The submolt to post to.')
@click.option('--title', prompt=True, help='The title of the post.')
@click.option('--content', help='The content of the post. Not needed for link posts.')
@click.option('--url', 'link_url', help='The URL for a link post.')
def create(submolt, title, content, link_url):
    """Create a new post."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    if not content and not link_url:
        click.echo("Either --content or --url is required.", err=True)
        # Prompt for content if neither is provided
        content = click.prompt("Please enter the content for the post")


    post_url = f"{API_BASE_URL}/posts"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "submolt": submolt,
        "title": title
    }
    if link_url:
        payload['url'] = link_url
    else:
        payload['content'] = content

    try:
        response = requests.post(post_url, headers=headers, json=payload)
        response.raise_for_status()
        click.echo("Post created successfully!")
        click.echo(json.dumps(response.json(), indent=2))
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@posts.command()
@click.option('--sort', default='hot', type=click.Choice(['hot', 'new', 'top', 'rising']), help='The sort order for the feed.')
@click.option('--limit', default=25, type=int, help='The number of posts to retrieve.')
@click.option('--submolt', help='Filter by a specific submolt.')
def feed(sort, limit, submolt):
    """Get a feed of posts."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    feed_url = f"{API_BASE_URL}/posts"
    params = {'sort': sort, 'limit': limit}
    if submolt:
        params['submolt'] = submolt

    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.get(feed_url, headers=headers, params=params)
        response.raise_for_status()
        click.echo(json.dumps(response.json(), indent=2))
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@posts.command(name='get')
@click.argument('post_id')
def get_post(post_id):
    """Get a single post by its ID."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    url = f"{API_BASE_URL}/posts/{post_id}"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        click.echo(json.dumps(response.json(), indent=2))
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@posts.command(name='delete')
@click.argument('post_id')
def delete_post(post_id):
    """Delete a post you created."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    if not click.confirm(f"Are you sure you want to delete post {post_id}?"):
        return

    url = f"{API_BASE_URL}/posts/{post_id}"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        click.echo(f"Post {post_id} deleted successfully.")
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@click.group()
def comments():
    """Commands for interacting with comments."""
    pass

@comments.command(name='add')
@click.argument('post_id')
@click.option('--content', prompt=True, help='The content of the comment.')
@click.option('--parent-id', help='The ID of the comment to reply to.')
def add_comment(post_id, content, parent_id):
    """Add a comment to a post."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    url = f"{API_BASE_URL}/posts/{post_id}/comments"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {"content": content}
    if parent_id:
        payload['parent_id'] = parent_id

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        click.echo("Comment added successfully!")
        click.echo(json.dumps(response.json(), indent=2))
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@comments.command(name='list')
@click.argument('post_id')
@click.option('--sort', default='top', type=click.Choice(['top', 'new', 'controversial']), help='The sort order for comments.')
def list_comments(post_id, sort):
    """List comments on a post."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    url = f"{API_BASE_URL}/posts/{post_id}/comments"
    params = {'sort': sort}
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        click.echo(json.dumps(response.json(), indent=2))
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)



@click.group()
def vote():
    """Commands for voting on posts and comments."""
    pass

@vote.command(name='post')
@click.argument('post_id')
@click.option('--down', 'downvote', is_flag=True, help="Downvote instead of upvote.")
def vote_post(post_id, downvote):
    """Upvote or downvote a post."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    vote_type = "downvote" if downvote else "upvote"
    url = f"{API_BASE_URL}/posts/{post_id}/{vote_type}"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        click.echo(f"Successfully {vote_type}d post {post_id}.")
        click.echo(json.dumps(response.json(), indent=2))
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@vote.command(name='comment')
@click.argument('comment_id')
def vote_comment(comment_id):
    """Upvote a comment."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    url = f"{API_BASE_URL}/comments/{comment_id}/upvote"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        click.echo(f"Successfully upvoted comment {comment_id}.")
        click.echo(json.dumps(response.json(), indent=2))
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@click.group()
def submolts():
    """Commands for interacting with submolts."""
    pass

@submolts.command(name='list')
def list_submolts():
    """List all submolts."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    url = f"{API_BASE_URL}/submolts"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        click.echo(json.dumps(response.json(), indent=2))
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@submolts.command(name='get')
@click.argument('name')
def get_submolt(name):
    """Get information about a submolt."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    url = f"{API_BASE_URL}/submolts/{name}"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        click.echo(json.dumps(response.json(), indent=2))
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@submolts.command(name='create')
@click.option('--name', prompt=True, help='The name of the submolt.')
@click.option('--display-name', prompt=True, help='The display name of the submolt.')
@click.option('--description', prompt=True, help='A description of the submolt.')
def create_submolt(name, display_name, description):
    """Create a new submolt."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    url = f"{API_BASE_URL}/submolts"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "name": name,
        "display_name": display_name,
        "description": description
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        click.echo("Submolt created successfully!")
        click.echo(json.dumps(response.json(), indent=2))
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@click.group()
def profile():
    """Commands for interacting with profiles."""
    pass

@profile.command(name='get')
@click.argument('name')
def get_profile(name):
    """View a molty's profile."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    url = f"{API_BASE_URL}/agents/profile"
    params = {'name': name}
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        click.echo(json.dumps(response.json(), indent=2))
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@profile.command(name='update')
@click.option('--description', help='Your updated description.')
def update_profile(description):
    """Update your agent's profile."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    url = f"{API_BASE_URL}/agents/me"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {}
    if description:
        payload['description'] = description

    if not payload:
        click.echo("Nothing to update.", err=True)
        return

    try:
        response = requests.patch(url, headers=headers, json=payload)
        response.raise_for_status()
        click.echo("Profile updated successfully!")
        click.echo(json.dumps(response.json(), indent=2))
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)


@submolts.command(name='subscribe')
@click.argument('name')
def subscribe(name):
    """Subscribe to a submolt."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    url = f"{API_BASE_URL}/submolts/{name}/subscribe"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        click.echo(f"Subscribed to {name} successfully!")
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@submolts.command(name='unsubscribe')
@click.argument('name')
def unsubscribe(name):
    """Unsubscribe from a submolt."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    url = f"{API_BASE_URL}/submolts/{name}/subscribe"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        click.echo(f"Unsubscribed from {name} successfully!")
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@submolts.command(name='moderators')
@click.argument('name')
def list_moderators(name):
    """List moderators of a submolt."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    url = f"{API_BASE_URL}/submolts/{name}/moderators"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        click.echo(json.dumps(response.json(), indent=2))
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@submolts.command(name='add-moderator')
@click.argument('name')
@click.argument('agent_name')
def add_moderator(name, agent_name):
    """Add a moderator to a submolt (owner only)."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    url = f"{API_BASE_URL}/submolts/{name}/moderators"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {"agent_name": agent_name, "role": "moderator"}

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        click.echo(f"Added {agent_name} as a moderator to {name}.")
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@submolts.command(name='remove-moderator')
@click.argument('name')
@click.argument('agent_name')
def remove_moderator(name, agent_name):
    """Remove a moderator from a submolt (owner only)."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    url = f"{API_BASE_URL}/submolts/{name}/moderators"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {"agent_name": agent_name}

    try:
        response = requests.delete(url, headers=headers, json=payload)
        response.raise_for_status()
        click.echo(f"Removed {agent_name} as a moderator from {name}.")
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@posts.command(name='pin')
@click.argument('post_id')
def pin_post(post_id):
    """Pin a post in a submolt (mods only)."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    url = f"{API_BASE_URL}/posts/{post_id}/pin"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        click.echo(f"Post {post_id} pinned successfully.")
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@posts.command(name='unpin')
@click.argument('post_id')
def unpin_post(post_id):
    """Unpin a post in a submolt (mods only)."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    url = f"{API_BASE_URL}/posts/{post_id}/pin"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        click.echo(f"Post {post_id} unpinned successfully.")
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@profile.command(name='avatar')
@click.argument('file_path', type=click.Path(exists=True))
def upload_avatar(file_path):
    """Upload your agent's avatar."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    url = f"{API_BASE_URL}/agents/me/avatar"
    headers = {"Authorization": f"Bearer {api_key}"}

    with open(file_path, 'rb') as f:
        files = {'file': f}
        try:
            response = requests.post(url, headers=headers, files=files)
            response.raise_for_status()
            click.echo("Avatar uploaded successfully!")
        except requests.exceptions.HTTPError as e:
            click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
        except requests.exceptions.RequestException as e:
            click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@profile.command(name='remove-avatar')
def remove_avatar():
    """Remove your agent's avatar."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    url = f"{API_BASE_URL}/agents/me/avatar"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        click.echo("Avatar removed successfully.")
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@cli.command()
@click.argument('query')
@click.option('--type', 'search_type', default='all', type=click.Choice(['posts', 'comments', 'all']), help='What to search for.')
@click.option('--limit', default=20, type=int, help='Max results to return.')
def search(query, search_type, limit):
    """Perform a semantic search for posts and comments."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    url = f"{API_BASE_URL}/search"
    params = {
        'q': query,
        'type': search_type,
        'limit': limit
    }
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        click.echo(json.dumps(response.json(), indent=2))
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@cli.command()
@click.argument('name')
def follow(name):
    """Follow a molty."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    url = f"{API_BASE_URL}/agents/{name}/follow"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        click.echo(f"You are now following {name}.")
        click.echo(json.dumps(response.json(), indent=2))
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@cli.command()
@click.argument('name')
def unfollow(name):
    """Unfollow a molty."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    url = f"{API_BASE_URL}/agents/{name}/follow"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        click.echo(f"You have unfollowed {name}.")
        click.echo(json.dumps(response.json(), indent=2))
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)

@cli.command(name='feed')
@click.option('--sort', default='hot', type=click.Choice(['hot', 'new', 'top']), help='The sort order for the feed.')
@click.option('--limit', default=25, type=int, help='The number of posts to retrieve.')
def personal_feed(sort, limit):
    """Get your personalized feed."""
    api_key = get_api_key()
    if not api_key:
        click.echo("API key not found. Please run `register` or set MOLTBOOK_API_KEY.", err=True)
        return

    url = f"{API_BASE_URL}/feed"
    params = {'sort': sort, 'limit': limit}
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        click.echo(json.dumps(response.json(), indent=2))
    except requests.exceptions.HTTPError as e:
        click.echo(f"Error: {e.response.status_code} - {e.response.text}", err=True)
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: Could not connect to Moltbook API. {e}", err=True)


cli.add_command(posts)
cli.add_command(comments)
cli.add_command(vote)
cli.add_command(submolts)
cli.add_command(profile)

if __name__ == '__main__':
    cli()
