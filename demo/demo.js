let count = 0;
document.querySelector('#test-button').addEventListener('click', () => { document.querySelector('#counter').textContent = `${++count} clicks`; });
