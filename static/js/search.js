(function() {
  var overlay = document.getElementById('search-overlay');
  var input = document.getElementById('search-input');
  var results = document.getElementById('search-results');
  var index = null;

  // Load search index
  function loadIndex() {
    if (index) return Promise.resolve(index);
    var baseMeta = document.querySelector('meta[name="base-url"]');
    var baseUrl = baseMeta ? baseMeta.content.replace(/\/$/, '') : '';
    return fetch(baseUrl + '/index.json')
      .then(function(r) { return r.json(); })
      .then(function(data) { index = data; return data; });
  }

  // Search
  function search(query) {
    if (!query || query.length < 1) {
      results.innerHTML = '';
      return;
    }
    loadIndex().then(function(data) {
      var q = query.toLowerCase();
      var matches = data.filter(function(item) {
        return item.title.toLowerCase().indexOf(q) !== -1 ||
               (item.description && item.description.toLowerCase().indexOf(q) !== -1) ||
               (item.tags && item.tags.toLowerCase().indexOf(q) !== -1);
      }).slice(0, 20);

      if (matches.length === 0) {
        results.innerHTML = '<div class="search-no-result">見つかりませんでした</div>';
        return;
      }

      results.innerHTML = matches.map(function(item) {
        return '<a href="' + item.permalink + '" class="search-result-item">' +
               '<div class="search-result-title">' + item.title + '</div>' +
               (item.description ? '<div class="search-result-desc">' + item.description.substring(0, 80) + '</div>' : '') +
               '</a>';
      }).join('');
    });
  }

  // Events
  if (input) {
    var timer;
    input.addEventListener('input', function() {
      clearTimeout(timer);
      timer = setTimeout(function() { search(input.value); }, 200);
    });
  }

  if (overlay) {
    overlay.addEventListener('click', function(e) {
      if (e.target === overlay) overlay.classList.remove('active');
    });
  }

  // Keyboard shortcut: Ctrl+K or / to open search
  document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey && e.key === 'k') || (e.key === '/' && !e.target.closest('input,textarea'))) {
      e.preventDefault();
      overlay.classList.add('active');
      input.focus();
    }
    if (e.key === 'Escape') {
      overlay.classList.remove('active');
    }
  });
})();
