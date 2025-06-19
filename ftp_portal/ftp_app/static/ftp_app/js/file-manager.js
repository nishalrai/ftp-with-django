function updateFilePaths(input, listId) {
    const fileList = document.getElementById(listId);
    fileList.innerHTML = '';

    if (!input.files || input.files.length === 0) return;

    const ul = document.createElement('ul');
    for (let i = 0; i < input.files.length; i++) {
        const file = input.files[i];
        // Show relative path if folder, else filename
        const displayName = file.webkitRelativePath || file.name;
        const li = document.createElement('li');
        li.textContent = displayName;
        ul.appendChild(li);
    }
    fileList.appendChild(ul);
}

function toggleFolder(element) {
    const contents = element.nextElementSibling;
    if (contents && contents.classList) {
        contents.classList.toggle('hidden');
    }
}

function toggleActionButtons() {
    const checkboxes = document.querySelectorAll('.file-checkbox');
    const deleteBtn = document.getElementById('deleteBtn');
    const renameBtn = document.getElementById('renameBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const shareBtn = document.getElementById('shareBtn');

    const checkedCount = Array.from(checkboxes).filter(cb => cb.checked).length;

    deleteBtn.disabled = checkedCount === 0;
    renameBtn.disabled = checkedCount === 0;
    downloadBtn.disabled = checkedCount !== 1;
    shareBtn.disabled = checkedCount === 0;
}

function showRenameForm() {
    const selectedCheckboxes = document.querySelectorAll('.file-checkbox:checked');
    if (selectedCheckboxes.length === 0) return;

    const renameInputs = document.getElementById('renameInputs');
    renameInputs.innerHTML = '';

    selectedCheckboxes.forEach(cb => {
        const oldName = cb.value;
        renameInputs.insertAdjacentHTML('beforeend', `
            <label class="block text-sm text-gray-600 break-all">${oldName}</label>
            <input type="hidden" name="old_names" value="${oldName}">
            <input type="text" name="new_names" value="${oldName}" class="w-full p-2 border rounded-lg mb-2" required>
        `);
    });

    document.getElementById('renameForm').classList.remove('hidden');
}

function hideRenameForm() {
    document.getElementById('renameForm').classList.add('hidden');
}

function showShareForm() {
    document.getElementById('shareForm').classList.remove('hidden');
}

function hideShareForm() {
    document.getElementById('shareForm').classList.add('hidden');
}

function copyLink(button) {
    const input = button.previousElementSibling;
    input.select();
    input.setSelectionRange(0, 99999); // For mobile
    navigator.clipboard.writeText(input.value).then(() => {
        alert('Link copied to clipboard!');
    }).catch(() => {
        alert('Failed to copy link.');
    });
}

// Drag and Drop support
document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    if (!dropZone) return;

    dropZone.addEventListener('dragover', e => {
        e.preventDefault();
        dropZone.classList.add('bg-gray-100');
    });

    dropZone.addEventListener('dragleave', e => {
        e.preventDefault();
        dropZone.classList.remove('bg-gray-100');
    });

    dropZone.addEventListener('drop', e => {
        e.preventDefault();
        dropZone.classList.remove('bg-gray-100');

        const dt = e.dataTransfer;
        const files = dt.files;

        // Detect if folder dropped
        let isFolder = false;
        if (dt.items) {
            for (let i = 0; i < dt.items.length; i++) {
                const entry = dt.items[i].webkitGetAsEntry && dt.items[i].webkitGetAsEntry();
                if (entry && entry.isDirectory) {
                    isFolder = true;
                    break;
                }
            }
        }

        const input = isFolder
            ? document.getElementById('folder-upload')
            : document.getElementById('file-upload');

        // Create a DataTransfer to set files programmatically (some browsers)
        const dataTransfer = new DataTransfer();
        for (let i = 0; i < files.length; i++) {
            dataTransfer.items.add(files[i]);
        }
        input.files = dataTransfer.files;

        updateFilePaths(input, 'file-list');
    });

    dropZone.addEventListener('click', () => {
        if (confirm('Select a folder? (Click "Cancel" to select files)')) {
            document.getElementById('folder-upload').click();
        } else {
            document.getElementById('file-upload').click();
        }
    });

    // Automatically reopen share form if links are generated
    if (document.getElementById('shareForm')?.querySelector('ul')) {
        showShareForm();
    }
});
