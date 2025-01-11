document.addEventListener('DOMContentLoaded', function() {
    const linksList = document.getElementById('links-list');
    if (linksList) {
        const userId = linksList.dataset.userId;
        loadLinks(userId);
    }
});

function loadLinks(userId) {
    const url = userId ? `/links/${userId}` : '/links';
    fetch(url)
        .then(response => response.json())
        .then(links => {
            const linksList = document.getElementById('links-list');
            linksList.innerHTML = '';
            
            if (links.length === 0) {
                linksList.innerHTML = '<p>No links added yet.</p>';
                return;
            }

            links.forEach(link => {
                const linkElement = createLinkElement(link);
                linksList.appendChild(linkElement);
            });
        })
        .catch(error => {
            console.error('Error loading links:', error);
            const linksList = document.getElementById('links-list');
            linksList.innerHTML = '<p>Error loading links. Please try again later.</p>';
        });
}

function createLinkElement(link) {
    const div = document.createElement('div');
    div.className = 'link-item';
    
    const title = document.createElement('h3');
    title.textContent = link.title;
    
    const description = document.createElement('p');
    description.className = 'description';
    description.textContent = link.description;
    
    const linksDiv = document.createElement('div');
    linksDiv.className = 'link-urls';
    
    if (link.demo_url) {
        const demoLink = createLinkButton('Demo Video', link.demo_url, 'demo');
        linksDiv.appendChild(demoLink);
    }
    
    if (link.github_url) {
        const githubLink = createLinkButton('GitHub', link.github_url, 'github');
        linksDiv.appendChild(githubLink);
    }
    
    if (link.webapp_url) {
        const webappLink = createLinkButton('Web App', link.webapp_url, 'webapp');
        linksDiv.appendChild(webappLink);
    }
    
    const date = document.createElement('p');
    date.className = 'date';
    date.textContent = new Date(link.created_at).toLocaleDateString();
    
    const shareUrl = `${window.location.origin}/embed/${link.id}`;
    const tweetText = `${link.title}\n\n${link.description || ''}\n\n${link.demo_url ? '🎥 Demo: ' + link.demo_url + '\n' : ''}${link.github_url ? '💻 Code: ' + link.github_url + '\n' : ''}${link.webapp_url ? '🌐 Live: ' + link.webapp_url : ''}`;
    const shareLink = document.createElement('a');
    shareLink.href = `https://twitter.com/intent/tweet?text=${encodeURIComponent(tweetText)}&url=${encodeURIComponent(shareUrl)}`;
    shareLink.className = 'share-button';
    shareLink.target = '_blank';
    shareLink.textContent = 'Share on X';
    
    div.appendChild(title);
    div.appendChild(description);
    div.appendChild(linksDiv);
    div.appendChild(date);
    div.appendChild(shareLink);
    
    return div;
}

function createLinkButton(text, url, type) {
    const link = document.createElement('a');
    link.href = url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.className = `link-type ${type}`;
    link.textContent = text;
    return link;
}
