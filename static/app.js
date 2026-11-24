// VivahEdit AI - Client-side Logic (English UI)

// Global modal close helpers accessible anywhere & from inline onclick
window.closeSettingsModal = function() {
  const m = document.getElementById('modalSettings');
  if (m) m.classList.add('hidden');
};

window.closeScannedFolderModal = function() {
  const m = document.getElementById('modalScannedCards');
  if (m) m.classList.add('hidden');
};

document.addEventListener('DOMContentLoaded', () => {
  // Register service worker if supported
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js').catch(err => console.log('SW registration failed:', err));
  }

  // State
  let currentCardFiles = [];
  let currentCardSide = 'groom';
  let weddingData = {};
  let groomPhotoFile = null;
  let bridePhotoFile = null;

  // Card side elements
  const btnSideGroom = document.getElementById('btnSideGroom');
  const btnSideBride = document.getElementById('btnSideBride');
  const badgeCardSide = document.getElementById('badgeCardSide');
  const cardSideNote = document.getElementById('cardSideNote');

  function updateHeaderProjectName() {
    const elHeaderName = document.getElementById('headerProjectName');
    const elHeaderSub = document.getElementById('headerProjectSub');
    if (!elHeaderName) return;

    const groom = (document.getElementById('inpGroomName')?.value || '').trim();
    const bride = (document.getElementById('inpBrideName')?.value || '').trim();
    const pariwar = (document.getElementById('inpPariwar')?.value || '').trim();

    if (currentCardSide === 'bride') {
      const primary = bride || groom;
      if (primary) {
        elHeaderName.textContent = primary;
        if (elHeaderSub) elHeaderSub.textContent = pariwar ? `${pariwar} • Bride Side` : 'Bride Side';
      } else {
        elHeaderName.textContent = 'VivahEdit AI';
        if (elHeaderSub) elHeaderSub.textContent = 'After Motion Z Automation';
      }
    } else {
      const primary = groom || bride;
      if (primary) {
        elHeaderName.textContent = primary;
        if (elHeaderSub) elHeaderSub.textContent = pariwar ? `${pariwar} • Groom Side` : 'Groom Side';
      } else {
        elHeaderName.textContent = 'VivahEdit AI';
        if (elHeaderSub) elHeaderSub.textContent = 'After Motion Z Automation';
      }
    }
  }

  function setCardSide(side) {
    currentCardSide = (side === 'bride') ? 'bride' : 'groom';
    if (!btnSideGroom || !btnSideBride) return;
    if (currentCardSide === 'bride') {
      btnSideBride.className = 'py-2 px-2 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1.5 bg-gradient-to-r from-pink-600 to-rose-600 text-white shadow';
      btnSideGroom.className = 'py-2 px-2 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1.5 text-white/60 hover:text-white';
      if (badgeCardSide) {
        badgeCardSide.className = 'text-[10px] bg-pink-500/20 text-pink-300 border border-pink-500/40 px-2.5 py-0.5 rounded-full font-bold';
        badgeCardSide.textContent = '👧 वधू पक्ष';
      }
      if (cardSideNote) {
        cardSideNote.textContent = "वधू पक्ष: दुल्हन और उसके परिवार का विवरण पहले दिखेगा।";
      }
    } else {
      btnSideGroom.className = 'py-2 px-2 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow';
      btnSideBride.className = 'py-2 px-2 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1.5 text-white/60 hover:text-white';
      if (badgeCardSide) {
        badgeCardSide.className = 'text-[10px] bg-blue-500/20 text-blue-300 border border-blue-500/40 px-2.5 py-0.5 rounded-full font-bold';
        badgeCardSide.textContent = '👦 वर पक्ष';
      }
      if (cardSideNote) {
        cardSideNote.textContent = "वर पक्ष: दूल्हे और उसके परिवार का विवरण पहले दिखेगा।";
      }
    }
    updateHeaderProjectName();
  }

  if (btnSideGroom) btnSideGroom.addEventListener('click', () => setCardSide('groom'));
  if (btnSideBride) btnSideBride.addEventListener('click', () => setCardSide('bride'));

  // Elements
  const navStep1 = document.getElementById('navStep1');
  const navStep2 = document.getElementById('navStep2');
  const navStep3 = document.getElementById('navStep3');

  const step1Section = document.getElementById('step1Section');
  const step2Section = document.getElementById('step2Section');
  const step3Section = document.getElementById('step3Section');

  const cardFileInput = document.getElementById('cardFileInput');
  const cardUploadPlaceholder = document.getElementById('cardUploadPlaceholder');
  const cardPreviewContainer = document.getElementById('cardPreviewContainer');
  const cardThumbnailsGrid = document.getElementById('cardThumbnailsGrid');
  const cardPagesBadge = document.getElementById('cardPagesBadge');
  const btnAddMoreCards = document.getElementById('btnAddMoreCards');

  const btnStartAiScan = document.getElementById('btnStartAiScan');
  const btnLoadDemo = document.getElementById('btnLoadDemo');
  const btnProceedToXml = document.getElementById('btnProceedToXml');
  const btnShareAfterMotion = document.getElementById('btnShareAfterMotion');
  const btnDownloadAmzip = document.getElementById('btnDownloadAmzip');
  const btnDownloadXml = document.getElementById('btnDownloadXml');
  const btnShareLabel = document.getElementById('btnShareLabel');
  const btnStartNew = document.getElementById('btnStartNew');

  // Couple Photos Elements (.amzip)
  const photoGroomInput = document.getElementById('photoGroomInput');
  const photoGroomPlaceholder = document.getElementById('photoGroomPlaceholder');
  const photoGroomPreview = document.getElementById('photoGroomPreview');
  const imgGroomPreview = document.getElementById('imgGroomPreview');
  const lblGroomPhotoName = document.getElementById('lblGroomPhotoName');
  const btnRemoveGroomPhoto = document.getElementById('btnRemoveGroomPhoto');

  const photoBrideInput = document.getElementById('photoBrideInput');
  const photoBridePlaceholder = document.getElementById('photoBridePlaceholder');
  const photoBridePreview = document.getElementById('photoBridePreview');
  const imgBridePreview = document.getElementById('imgBridePreview');
  const lblBridePhotoName = document.getElementById('lblBridePhotoName');
  const btnRemoveBridePhoto = document.getElementById('btnRemoveBridePhoto');

  function updatePhotoUiState() {
    if (groomPhotoFile) {
      if (photoGroomPlaceholder) photoGroomPlaceholder.classList.add('hidden');
      if (photoGroomPreview) photoGroomPreview.classList.remove('hidden');
      if (lblGroomPhotoName) lblGroomPhotoName.textContent = groomPhotoFile.name;
    } else {
      if (photoGroomPlaceholder) photoGroomPlaceholder.classList.remove('hidden');
      if (photoGroomPreview) photoGroomPreview.classList.add('hidden');
      if (imgGroomPreview) imgGroomPreview.src = '';
      if (photoGroomInput) photoGroomInput.value = '';
    }

    if (bridePhotoFile) {
      if (photoBridePlaceholder) photoBridePlaceholder.classList.add('hidden');
      if (photoBridePreview) photoBridePreview.classList.remove('hidden');
      if (lblBridePhotoName) lblBridePhotoName.textContent = bridePhotoFile.name;
    } else {
      if (photoBridePlaceholder) photoBridePlaceholder.classList.remove('hidden');
      if (photoBridePreview) photoBridePreview.classList.add('hidden');
      if (imgBridePreview) imgBridePreview.src = '';
      if (photoBrideInput) photoBrideInput.value = '';
    }

    if (btnShareLabel) {
      if (groomPhotoFile || bridePhotoFile) {
        btnShareLabel.textContent = '1-Tap Open .amzip with After Motion Z (With Photos)';
      } else {
        btnShareLabel.textContent = '1-Tap Open with After Motion Z';
      }
    }
  }

  if (photoGroomInput) {
    photoGroomInput.addEventListener('change', (e) => {
      const file = e.target.files && e.target.files[0];
      if (file) {
        groomPhotoFile = file;
        if (imgGroomPreview) imgGroomPreview.src = URL.createObjectURL(file);
        updatePhotoUiState();
        showToast('Groom photo selected!', 'info');
      }
    });
  }

  if (btnRemoveGroomPhoto) {
    btnRemoveGroomPhoto.addEventListener('click', (e) => {
      e.stopPropagation();
      groomPhotoFile = null;
      updatePhotoUiState();
    });
  }

  if (photoBrideInput) {
    photoBrideInput.addEventListener('change', (e) => {
      const file = e.target.files && e.target.files[0];
      if (file) {
        bridePhotoFile = file;
        if (imgBridePreview) imgBridePreview.src = URL.createObjectURL(file);
        updatePhotoUiState();
        showToast('Bride photo selected!', 'info');
      }
    });
  }

  if (btnRemoveBridePhoto) {
    btnRemoveBridePhoto.addEventListener('click', (e) => {
      e.stopPropagation();
      bridePhotoFile = null;
      updatePhotoUiState();
    });
  }

  const loadingOverlay = document.getElementById('loadingOverlay');
  const loadingTitle = document.getElementById('loadingTitle');
  const loadingSub = document.getElementById('loadingSub');

  // Modals
  const modalQr = document.getElementById('modalQr');
  const btnOpenQr = document.getElementById('btnOpenQr');
  const btnCloseQr = document.getElementById('btnCloseQr');
  const mobileUrlDisplay = document.getElementById('mobileUrlDisplay');

  const modalSettings = document.getElementById('modalSettings');
  const btnSettings = document.getElementById('btnSettings');
  const btnCloseSettings = document.getElementById('btnCloseSettings');
  const inpApiKey = document.getElementById('inpApiKey');
  const btnSaveApiKey = document.getElementById('btnSaveApiKey');

  // Load Saved API key if input exists
  if (inpApiKey) {
    let savedKey = localStorage.getItem('gemini_api_key');
    if (savedKey) inpApiKey.value = savedKey;

    const btnToggleKeyVis = document.getElementById('btnToggleKeyVis');
    const eyeIcon = document.getElementById('eyeIcon');
    if (btnToggleKeyVis) {
      btnToggleKeyVis.addEventListener('click', () => {
        if (inpApiKey.type === 'password') {
          inpApiKey.type = 'text';
          if (eyeIcon) eyeIcon.className = 'fa-solid fa-eye-slash';
        } else {
          inpApiKey.type = 'password';
          if (eyeIcon) eyeIcon.className = 'fa-solid fa-eye';
        }
      });
    }
  }

  // ==================== MULTI-EDITOR WORKSPACE CONTROLLER ====================
  let currentEditor = null;
  try {
    currentEditor = JSON.parse(localStorage.getItem('current_editor') || 'null');
  } catch (_) {
    currentEditor = null;
  }

  function getCurrentEditorId() {
    return (currentEditor && currentEditor.id) ? currentEditor.id : (localStorage.getItem('current_editor_id') || 'amar');
  }

  function updateActiveEditorUi() {
    const editorId = getCurrentEditorId();
    const name = (currentEditor && currentEditor.name) ? currentEditor.name : (editorId.charAt(0).toUpperCase() + editorId.slice(1));
    const icon = (currentEditor && currentEditor.avatar) ? currentEditor.avatar : 'fa-crown';

    const elHeaderName = document.getElementById('headerEditorName');
    const elHeaderIcon = document.getElementById('headerEditorIcon');
    if (elHeaderName) elHeaderName.textContent = name;
    if (elHeaderIcon) elHeaderIcon.className = `fa-solid ${icon} text-[11px] text-amber-400`;

    const elSettingsName = document.getElementById('settingsEditorName');
    const elSettingsIcon = document.getElementById('settingsEditorIcon');
    if (elSettingsName) elSettingsName.textContent = name;
    if (elSettingsIcon) elSettingsIcon.className = `fa-solid ${icon}`;

    const elNoTplName = document.getElementById('noTemplatesEditorName');
    if (elNoTplName) elNoTplName.textContent = name;

    const elBadge = document.getElementById('settingsEditorTemplateBadge');
    if (elBadge) elBadge.textContent = name;
  }

  const editorSelectionScreen = document.getElementById('editorSelectionScreen');
  const editorProfilesGrid = document.getElementById('editorProfilesGrid');
  const btnCloseEditorModal = document.getElementById('btnCloseEditorModal');
  const btnOpenMasterPasscode = document.getElementById('btnOpenMasterPasscode');
  const btnBackToEditorSelect = document.getElementById('btnBackToEditorSelect');

  window.openEditorSelectionModal = async function() {
    if (!editorSelectionScreen) return;
    editorSelectionScreen.classList.remove('hidden');
    if (btnCloseEditorModal) {
      if (currentEditor && getAuthToken()) {
        btnCloseEditorModal.classList.remove('hidden');
      } else {
        btnCloseEditorModal.classList.add('hidden');
      }
    }
    await loadEditorProfiles();
  };

  window.closeEditorSelectionModal = function() {
    if (editorSelectionScreen) editorSelectionScreen.classList.add('hidden');
  };

  async function loadEditorProfiles() {
    if (!editorProfilesGrid) return;
    editorProfilesGrid.innerHTML = '<div class="py-6 text-center text-white/50 text-xs"><i class="fa-solid fa-spinner animate-spin mr-2"></i>Loading profiles...</div>';
    try {
      const resp = await fetch('/api/editors');
      const data = await resp.json();
      const editors = (data && data.editors) || [];
      const currentId = getCurrentEditorId();

      editorProfilesGrid.innerHTML = '';
      editors.forEach(ed => {
        const isCurrent = (ed.id.toLowerCase() === currentId.toLowerCase());
        const card = document.createElement('div');
        card.className = `p-3.5 rounded-2xl bg-white/5 hover:bg-white/10 border ${isCurrent ? 'border-amber-400/80 bg-amber-500/10' : 'border-white/10'} flex items-center justify-between cursor-pointer transition shadow-md group active:scale-[0.99]`;
        card.onclick = () => selectEditorProfile(ed.id);

        card.innerHTML = `
          <div class="flex items-center gap-3 min-w-0">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-tr ${ed.color || 'from-amber-500 to-rose-600'} text-white flex items-center justify-center text-base shadow shrink-0">
              <i class="fa-solid ${ed.avatar || 'fa-user'}"></i>
            </div>
            <div class="min-w-0 text-left">
              <h3 class="text-sm font-bold text-white group-hover:text-amber-300 transition">${ed.name}</h3>
              <p class="text-[11px] text-white/50">${ed.templates_count} XML Templates</p>
            </div>
          </div>
          <div class="flex items-center gap-1.5 text-xs ${isCurrent ? 'text-black bg-amber-400 font-bold' : 'text-amber-300 bg-amber-500/20 group-hover:bg-amber-500 group-hover:text-black font-semibold'} transition px-3 py-1.5 rounded-xl border border-amber-500/30 shrink-0">
            <span>${isCurrent ? 'Active' : 'Open'}</span>
            <i class="fa-solid ${isCurrent ? 'fa-check' : 'fa-arrow-right'} text-[10px]"></i>
          </div>
        `;
        editorProfilesGrid.appendChild(card);
      });
    } catch (e) {
      editorProfilesGrid.innerHTML = `<div class="p-4 text-center text-rose-400 text-xs">Error: ${e.message}</div>`;
    }
  }

  window.selectEditorProfile = async function(editorId) {
    if (!editorId) return;
    try {
      showLoading(true, 'Loading Workspace...', 'Selecting Editor Profile');
      const resp = await fetch('/api/editors/select', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ editor_id: editorId })
      });
      const data = await resp.json();
      if (resp.ok && data.success) {
        setAuthToken(data.token, true);
        currentEditor = data.editor;
        localStorage.setItem('current_editor', JSON.stringify(data.editor));
        localStorage.setItem('current_editor_id', data.editor.id);
        document.documentElement.classList.add('has-auth-token');
        document.documentElement.classList.add('has-editor-profile');

        closeEditorSelectionModal();
        showGatekeeperScreen(false);
        updateActiveEditorUi();
        loadTemplates();
        showToast(`${data.editor.name}'s workspace unlocked!`, 'success');
      } else {
        showToast(data.detail || data.error || 'Failed to select editor profile', 'error');
      }
    } catch (err) {
      showToast('Error: ' + err.message, 'error');
    } finally {
      showLoading(false);
    }
  };

  if (btnOpenMasterPasscode) {
    btnOpenMasterPasscode.addEventListener('click', () => {
      closeEditorSelectionModal();
      showGatekeeperScreen(true);
    });
  }

  if (btnBackToEditorSelect) {
    btnBackToEditorSelect.addEventListener('click', () => {
      showGatekeeperScreen(false);
      openEditorSelectionModal();
    });
  }

  if (btnOpenMasterPasscode) {
    btnOpenMasterPasscode.addEventListener('click', () => {
      closeEditorSelectionModal();
      showGatekeeperScreen(true);
    });
  }

  if (btnBackToEditorSelect) {
    btnBackToEditorSelect.addEventListener('click', () => {
      showGatekeeperScreen(false);
      openEditorSelectionModal();
    });
  }

  // ==================== GATEKEEPER SECURITY CONTROLLER ====================
  function getAuthToken() {
    return localStorage.getItem('editor_access_token') || sessionStorage.getItem('editor_access_token') || '';
  }

  function setAuthToken(token, remember = true) {
    if (remember) {
      localStorage.setItem('editor_access_token', token);
      sessionStorage.removeItem('editor_access_token');
    } else {
      sessionStorage.setItem('editor_access_token', token);
      localStorage.removeItem('editor_access_token');
    }
  }

  function clearAuthToken() {
    localStorage.removeItem('editor_access_token');
    sessionStorage.removeItem('editor_access_token');
    localStorage.removeItem('current_editor_id');
    localStorage.removeItem('current_editor');
  }

  async function authFetch(url, options = {}) {
    const token = getAuthToken();
    const editorId = getCurrentEditorId();
    options.headers = options.headers || {};
    if (token) {
      if (options.headers instanceof Headers) {
        options.headers.set('X-Access-Token', token);
        options.headers.set('X-Editor-Id', editorId);
      } else {
        options.headers['X-Access-Token'] = token;
        options.headers['X-Editor-Id'] = editorId;
      }
    }
    const resp = await fetch(url, options);
    if (resp.status === 401 && !url.includes('/api/auth/') && !url.includes('/api/editors/')) {
      openEditorSelectionModal();
      showToast('Workspace locked. Please select your editor profile.', 'error');
    }
    return resp;
  }

  const gatekeeperScreen = document.getElementById('gatekeeperScreen');
  const inpGatekeeperPass = document.getElementById('inpGatekeeperPass');
  const btnToggleGatekeeperEye = document.getElementById('btnToggleGatekeeperEye');
  const gatekeeperEyeIcon = document.getElementById('gatekeeperEyeIcon');
  const chkRememberDevice = document.getElementById('chkRememberDevice');
  const btnUnlockGatekeeper = document.getElementById('btnUnlockGatekeeper');
  const gatekeeperErrorMsg = document.getElementById('gatekeeperErrorMsg');
  const btnLockApp = document.getElementById('btnLockApp');

  function showGatekeeperScreen(show) {
    if (!gatekeeperScreen) return;
    if (show) {
      gatekeeperScreen.classList.remove('hidden');
      if (gatekeeperErrorMsg) gatekeeperErrorMsg.classList.add('hidden');
      if (inpGatekeeperPass) {
        inpGatekeeperPass.value = '';
        setTimeout(() => inpGatekeeperPass.focus(), 150);
      }
    } else {
      gatekeeperScreen.classList.add('hidden');
    }
  }

  async function checkInitialAuth() {
    const token = getAuthToken();
    const editorId = localStorage.getItem('current_editor_id');
    if (!token || !editorId) {
      openEditorSelectionModal();
      return;
    }
    try {
      const resp = await fetch('/api/auth/check', {
        headers: {
          'X-Access-Token': token,
          'X-Editor-Id': editorId
        }
      });
      const data = await resp.json();
      if (data.authenticated) {
        if (data.editor) {
          currentEditor = data.editor;
          localStorage.setItem('current_editor', JSON.stringify(data.editor));
        }
        updateActiveEditorUi();
        closeEditorSelectionModal();
        showGatekeeperScreen(false);
        loadTemplates();
      } else {
        clearAuthToken();
        openEditorSelectionModal();
      }
    } catch (_) {
      openEditorSelectionModal();
    }
  }

  async function unlockGatekeeper() {
    const pass = (inpGatekeeperPass?.value || '').trim();
    if (!pass) {
      if (gatekeeperErrorMsg) {
        gatekeeperErrorMsg.textContent = 'Please enter passcode!';
        gatekeeperErrorMsg.classList.remove('hidden');
      }
      return;
    }

    if (btnUnlockGatekeeper) {
      btnUnlockGatekeeper.disabled = true;
      btnUnlockGatekeeper.innerHTML = '<i class="fa-solid fa-spinner animate-spin text-xs"></i><span>Verifying...</span>';
    }

    try {
      const resp = await fetch('/api/auth/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: pass })
      });
      const data = await resp.json();

      if (resp.ok && data.success) {
        const remember = chkRememberDevice ? chkRememberDevice.checked : true;
        setAuthToken(data.token, remember);
        document.documentElement.classList.add('has-auth-token');
        showGatekeeperScreen(false);
        closeEditorSelectionModal();
        updateActiveEditorUi();
        loadTemplates();
        showToast('Workspace unlocked!', 'success');
      } else {
        if (gatekeeperErrorMsg) {
          gatekeeperErrorMsg.textContent = data.error || 'Incorrect passcode!';
          gatekeeperErrorMsg.classList.remove('hidden');
        }
        if (inpGatekeeperPass) {
          inpGatekeeperPass.value = '';
          inpGatekeeperPass.focus();
        }
      }
    } catch (e) {
      if (gatekeeperErrorMsg) {
        gatekeeperErrorMsg.textContent = 'Network error: ' + e.message;
        gatekeeperErrorMsg.classList.remove('hidden');
      }
    } finally {
      if (btnUnlockGatekeeper) {
        btnUnlockGatekeeper.disabled = false;
        btnUnlockGatekeeper.innerHTML = '<i class="fa-solid fa-lock-open text-xs"></i><span>Unlock Workspace</span>';
      }
    }
  }

  if (btnUnlockGatekeeper) btnUnlockGatekeeper.addEventListener('click', unlockGatekeeper);
  if (inpGatekeeperPass) {
    inpGatekeeperPass.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') unlockGatekeeper();
    });
  }

  if (btnToggleGatekeeperEye) {
    btnToggleGatekeeperEye.addEventListener('click', () => {
      if (inpGatekeeperPass.type === 'password') {
        inpGatekeeperPass.type = 'text';
        gatekeeperEyeIcon.className = 'fa-solid fa-eye-slash';
      } else {
        inpGatekeeperPass.type = 'password';
        gatekeeperEyeIcon.className = 'fa-solid fa-eye';
      }
    });
  }

  if (btnLockApp) {
    btnLockApp.addEventListener('click', () => {
      clearAuthToken();
      document.documentElement.classList.remove('has-auth-token');
      document.documentElement.classList.remove('has-editor-profile');
      openEditorSelectionModal();
      showToast('Workspace locked', 'info');
    });
  }

  // Load Server Info for QR
  fetch('/api/info')
    .then(r => r.json())
    .then(data => {
      mobileUrlDisplay.textContent = data.mobile_url;
    })
    .catch(() => {});

  // Load Templates List with Multi-Editor Isolation & Permanent Storage
  function loadTemplates(selectedId = null) {
    const editorId = getCurrentEditorId();
    updateActiveEditorUi();
    authFetch(`/api/templates?editor_id=${encodeURIComponent(editorId)}`)
      .then(r => r.json())
      .then(data => {
        const templates = data.templates || [];
        const serverDefault = data.default_template;
        const savedPref = localStorage.getItem(`preferred_template_id_${editorId}`);

        // Target template priority: explicitly requested > localStorage > server default > first in list
        let activeId = selectedId;
        if (!activeId) {
          if (savedPref && templates.some(t => t.id === savedPref)) {
            activeId = savedPref;
          } else if (serverDefault && templates.some(t => t.id === serverDefault)) {
            activeId = serverDefault;
          } else if (templates.length > 0) {
            activeId = templates[0].id;
          }
        }

        // Save active template preference locally for this editor
        if (activeId) {
          localStorage.setItem(`preferred_template_id_${editorId}`, activeId);
        }

        // 1. Check if editor has 0 templates
        const noNotice = document.getElementById('noTemplatesNoticeStep3');
        const sel = document.getElementById('selectTemplate');
        const step1Badge = document.getElementById('step1ActiveTemplateBadge');

        if (templates.length === 0) {
          if (noNotice) noNotice.classList.remove('hidden');
          const noName = document.getElementById('noTemplatesEditorName');
          if (noName && currentEditor) noName.textContent = currentEditor.name;
          if (sel) {
            sel.innerHTML = '<option value="">No XML template found (+ Upload XML)</option>';
            sel.disabled = true;
          }
          if (step1Badge) step1Badge.textContent = '+ Upload XML Template';
        } else {
          if (noNotice) noNotice.classList.add('hidden');
          if (sel) {
            sel.disabled = false;
            sel.innerHTML = '';
            templates.forEach(t => {
              const opt = document.createElement('option');
              opt.value = t.id;
              const isDef = (t.id === serverDefault);
              opt.textContent = (isDef ? '⭐ ' : '') + t.name + (isDef ? ' (Default)' : '');
              if (activeId && (t.id === activeId || t.id.toLowerCase() === activeId.toLowerCase())) {
                opt.selected = true;
              }
              sel.appendChild(opt);
            });
          }
          if (step1Badge) {
            const currentTpl = templates.find(t => t.id === activeId) || templates[0];
            if (currentTpl) {
              step1Badge.textContent = currentTpl.name;
            }
          }
        }

        // 2. Populate Settings Modal Template Manager
        const settingsList = document.getElementById('settingsTemplatesList');
        if (settingsList) {
          settingsList.innerHTML = '';
          if (templates.length === 0) {
            settingsList.innerHTML = `<div class="p-3 text-center text-white/50 text-xs">No XML templates uploaded yet. Click [+ Upload XML] above to add.</div>`;
          } else {
            templates.forEach(t => {
              const isDef = (t.id === serverDefault);
              const row = document.createElement('div');
              row.className = 'flex items-center justify-between py-2 px-3 rounded-xl bg-white/5 border ' +
                (isDef ? 'border-amber-400/40 bg-amber-500/10' : 'border-white/5') + ' text-xs gap-2 transition';

              row.innerHTML = `
                <div class="flex items-center gap-2 min-w-0 text-left">
                  <i class="fa-solid fa-file-code ${isDef ? 'text-amber-400' : 'text-white/40'} text-xs shrink-0"></i>
                  <div class="min-w-0">
                    <div class="font-bold text-white truncate text-[11px]">${t.name}</div>
                    <div class="text-[9px] text-white/40">${t.size_kb ? t.size_kb + ' KB' : ''}</div>
                  </div>
                </div>
                <div class="flex items-center gap-1.5 shrink-0">
                  ${isDef ? `
                    <span class="text-[9px] bg-amber-500/20 text-amber-300 border border-amber-500/40 px-2 py-0.5 rounded-full font-bold">
                      Default
                    </span>
                  ` : `
                    <button type="button" onclick="setTemplateAsDefault('${t.id}')" class="px-2 py-1 rounded-lg bg-white/10 hover:bg-amber-500/20 text-white hover:text-amber-300 text-[10px] font-semibold transition border border-white/10 active:scale-95 cursor-pointer" title="Make this template default">
                      Set Default
                    </button>
                  `}
                  ${!t.is_system ? `
                    <button type="button" onclick="deleteCustomTemplate('${t.id}')" class="w-6 h-6 rounded-lg bg-rose-500/10 hover:bg-rose-600 text-rose-400 hover:text-white text-[10px] flex items-center justify-center transition border border-rose-500/20 active:scale-95 cursor-pointer" title="Delete template">
                      <i class="fa-solid fa-trash-can"></i>
                    </button>
                  ` : ''}
                </div>
              `;
              settingsList.appendChild(row);
            });
          }
        }
      })
      .catch(() => {});
  }

  // Make Template Default Permanently on Server & Client
  window.setTemplateAsDefault = async function(templateId) {
    if (!templateId) return;
    const editorId = getCurrentEditorId();
    try {
      showLoading(true, 'Saving Template as Default...', 'Permanently saving your preference');
      const res = await authFetch('/api/templates/set-default', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ template_id: templateId, editor_id: editorId })
      });
      const json = await res.json().catch(() => ({}));
      if (res.ok && json.success) {
        localStorage.setItem(`preferred_template_id_${editorId}`, templateId);
        showToast('Template set as default!', 'success');
        loadTemplates(templateId);
      } else {
        showToast(json.detail || 'Failed to set default template', 'error');
      }
    } catch (err) {
      showToast('Error: ' + err.message, 'error');
    } finally {
      showLoading(false);
    }
  };

  // Delete Custom Template Permanently
  window.deleteCustomTemplate = async function(templateId) {
    if (!templateId) return;
    const editorId = getCurrentEditorId();
    if (!confirm(`Are you sure you want to delete this template?\n${templateId}`)) return;
    try {
      showLoading(true, 'Deleting Template...', 'Removing custom template');
      const res = await authFetch(`/api/templates/${encodeURIComponent(templateId)}?editor_id=${encodeURIComponent(editorId)}`, {
        method: 'DELETE'
      });
      const json = await res.json().catch(() => ({}));
      if (res.ok && json.success) {
        if (localStorage.getItem(`preferred_template_id_${editorId}`) === templateId) {
          localStorage.removeItem(`preferred_template_id_${editorId}`);
        }
        showToast('Template deleted successfully', 'info');
        loadTemplates();
      } else {
        showToast(json.detail || 'Failed to delete template', 'error');
      }
    } catch (err) {
      showToast('Error: ' + err.message, 'error');
    } finally {
      showLoading(false);
    }
  };

  // Template dropdown change listener: auto-saves as permanent default!
  const selTemplate = document.getElementById('selectTemplate');
  if (selTemplate) {
    selTemplate.addEventListener('change', async (e) => {
      const chosenId = e.target.value;
      const editorId = getCurrentEditorId();
      if (chosenId) {
        localStorage.setItem(`preferred_template_id_${editorId}`, chosenId);
        authFetch('/api/templates/set-default', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ template_id: chosenId, editor_id: editorId })
        }).then(r => r.json()).then(data => {
          if (data.success) {
            showToast('Default template saved!', 'success');
            loadTemplates(chosenId);
          }
        }).catch(() => {});
      }
    });
  }

  // Step 1 Change Template button
  const btnStep1ChangeTemplate = document.getElementById('btnStep1ChangeTemplate');
  if (btnStep1ChangeTemplate) {
    btnStep1ChangeTemplate.addEventListener('click', () => {
      if (typeof window.openSettingsModal === 'function') {
        window.openSettingsModal();
      } else if (modalSettings) {
        modalSettings.classList.remove('hidden');
      }
      setTimeout(() => {
        const settingsList = document.getElementById('settingsTemplatesList');
        if (settingsList) {
          settingsList.scrollIntoView({ behavior: 'smooth' });
        }
      }, 150);
    });
  }

  // Check auth immediately
  checkInitialAuth();
  loadTemplates();

  // Unified Template Upload Handler (Supports .xml, .xml.txt, .amzip, .zip & Auto-Content Detection)
  async function handleTemplateUpload(file) {
    if (!file) return;

    let fileName = (file.name || 'template.xml').trim();
    let lowerName = fileName.toLowerCase();
    let fileToUpload = file;

    // Deep content inspection: check first 3KB for XML tags
    let isXmlByContent = false;
    try {
      const slice = file.slice(0, 3072);
      const text = await slice.text();
      if (text.includes('<scene') || text.includes('<?xml') || text.includes('<project') || text.includes('<alight')) {
        isXmlByContent = true;
      }
    } catch (_) {}

    const isZip = lowerName.endsWith('.amzip') || lowerName.endsWith('.zip');
    const isXmlExt = lowerName.endsWith('.xml') || lowerName.endsWith('.xml.txt');

    if (!isXmlExt && !isZip && !isXmlByContent) {
      showToast(`File is not XML or AMZIP (${fileName}). Please select an Alight Motion file!`, 'error');
      return;
    }

    // Auto-fix filename if Android / WhatsApp appended .txt or if extension was missing
    if (lowerName.endsWith('.xml.txt')) {
      fileName = fileName.replace(/\.xml\.txt$/i, '.xml');
      fileToUpload = new File([file], fileName, { type: 'application/xml' });
    } else if (!lowerName.endsWith('.xml') && !isZip && isXmlByContent) {
      fileName = fileName.replace(/\.[^/.]+$/, '') + '.xml';
      fileToUpload = new File([file], fileName, { type: 'application/xml' });
    }

    showLoading(true, 'Uploading XML Template...', 'Saving permanently and updating default');
    try {
      const fd = new FormData();
      fd.append('file', fileToUpload);
      fd.append('editor_id', getCurrentEditorId());
      const res = await authFetch('/api/templates/upload', {
        method: 'POST',
        body: fd
      });
      const json = await res.json().catch(() => ({}));
      if (res.ok && json.success) {
        localStorage.setItem(`preferred_template_id_${getCurrentEditorId()}`, json.filename);
        showToast(`🎉 Template "${json.name || json.filename}" uploaded and set active!`, 'success');
        loadTemplates(json.filename);
      } else {
        const errMsg = json.detail || json.error || ('Upload failed with status ' + res.status);
        showToast(errMsg, 'error');
      }
    } catch (err) {
      showToast('Upload error: ' + err.message, 'error');
    } finally {
      showLoading(false);
    }
  }

  // Template Upload Listeners (Step 3, Step 3 Empty State and Settings Modal)
  const templateFileInput = document.getElementById('templateFileInput');
  if (templateFileInput) {
    templateFileInput.addEventListener('change', (e) => {
      const file = e.target.files && e.target.files[0];
      if (file) handleTemplateUpload(file);
      templateFileInput.value = '';
    });
  }

  const step3EmptyUploadInput = document.getElementById('step3EmptyUploadInput');
  if (step3EmptyUploadInput) {
    step3EmptyUploadInput.addEventListener('change', (e) => {
      const file = e.target.files && e.target.files[0];
      if (file) handleTemplateUpload(file);
      step3EmptyUploadInput.value = '';
    });
  }

  const settingsTemplateFileInput = document.getElementById('settingsTemplateFileInput');
  if (settingsTemplateFileInput) {
    settingsTemplateFileInput.addEventListener('change', (e) => {
      const file = e.target.files && e.target.files[0];
      if (file) handleTemplateUpload(file);
      settingsTemplateFileInput.value = '';
    });
  }

  // Navigation Tabs
  let currentActiveStep = 1;

  function updateHeaderWatchCardButton() {
    const btn = document.getElementById('btnHeaderWatchCard');
    if (!btn) return;
    btn.classList.remove('hidden');
  }

  function showStep(stepNum, pushToHistory = true) {
    step1Section.classList.add('hidden');
    step2Section.classList.add('hidden');
    step3Section.classList.add('hidden');

    const inactiveClass = 'step-btn py-2 text-center rounded-xl transition text-white/60 hover:text-white flex items-center justify-center gap-1.5 text-xs font-semibold';
    const activeClass = 'step-btn py-2 text-center rounded-xl transition bg-gradient-to-r from-rose-700 to-amber-600 text-white shadow font-bold flex items-center justify-center gap-1.5 text-xs';

    navStep1.className = inactiveClass;
    navStep2.className = inactiveClass;
    navStep3.className = inactiveClass;

    currentActiveStep = stepNum;

    if (stepNum === 1) {
      step1Section.classList.remove('hidden');
      navStep1.className = activeClass;
      if (typeof closeCardSidebar === 'function') closeCardSidebar();
      else if (typeof closeFloatingWidget === 'function') closeFloatingWidget();
      if (typeof updateSidebarEdgeTabVisibility === 'function') updateSidebarEdgeTabVisibility();
    } else if (stepNum === 2) {
      step2Section.classList.remove('hidden');
      navStep2.className = activeClass;
      if (typeof updateSidebarEdgeTabVisibility === 'function') updateSidebarEdgeTabVisibility();
    } else if (stepNum === 3) {
      step3Section.classList.remove('hidden');
      navStep3.className = activeClass;
      if (typeof renderSummaryCard === 'function' && typeof getFormData === 'function') {
        renderSummaryCard(getFormData());
      }
      if (typeof updateSidebarEdgeTabVisibility === 'function') updateSidebarEdgeTabVisibility();
    }

    updateHeaderWatchCardButton();

    if (pushToHistory && window.history && window.history.pushState) {
      const state = window.history.state;
      if (!state || state.step !== stepNum) {
        window.history.pushState({ step: stepNum }, '');
      }
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  navStep1.addEventListener('click', () => showStep(1));
  navStep2.addEventListener('click', () => showStep(2));
  navStep3.addEventListener('click', () => showStep(3));

  const btnBackToStep1 = document.getElementById('btnBackToStep1');
  if (btnBackToStep1) btnBackToStep1.addEventListener('click', () => showStep(1));

  const btnBackToStep2 = document.getElementById('btnBackToStep2');
  if (btnBackToStep2) btnBackToStep2.addEventListener('click', () => showStep(2));

  // Multi-file and PDF rendering with Full Card View
  function renderCardThumbnails() {
    if (currentCardFiles.length === 0) {
      cardUploadPlaceholder.classList.remove('hidden');
      cardPreviewContainer.classList.add('hidden');
      cardFileInput.value = '';
      if (typeof updateFloatingCardView === 'function') updateFloatingCardView();
      if (typeof updateHeaderWatchCardButton === 'function') updateHeaderWatchCardButton();
      if (typeof updateSidebarEdgeTabVisibility === 'function') updateSidebarEdgeTabVisibility();
      return;
    }

    cardUploadPlaceholder.classList.add('hidden');
    cardPreviewContainer.classList.remove('hidden');

    if (typeof updateHeaderWatchCardButton === 'function') updateHeaderWatchCardButton();
    if (typeof updateSidebarEdgeTabVisibility === 'function') updateSidebarEdgeTabVisibility();

    const num = currentCardFiles.length;
    cardPagesBadge.textContent = `${num} ${num === 1 ? 'file' : 'files/pages'} ready`;
    cardThumbnailsGrid.innerHTML = '';

    // If single card uploaded: Display compact card preview with quick-view
    if (num === 1) {
      const file = currentCardFiles[0];
      const isPdf = file.name.toLowerCase().endsWith('.pdf') || file.type.includes('pdf');
      const card = document.createElement('div');
      card.className = 'relative rounded-xl overflow-hidden bg-black/40 border border-white/10 p-1.5 text-center group cursor-zoom-in hover:border-amber-400/40 transition';

      let innerHtml = '';
      if (isPdf) {
        innerHtml = `
          <div class="relative w-full rounded-xl bg-gradient-to-br from-purple-950/40 via-black to-black p-4 h-[260px] sm:h-[320px] flex flex-col items-center justify-center border border-white/10 shadow-inner">
            <div class="w-14 h-14 rounded-2xl bg-amber-500/20 text-amber-300 flex items-center justify-center text-3xl mb-2 border border-amber-500/30">
              <i class="fa-solid fa-file-pdf"></i>
            </div>
            <span class="text-sm font-bold text-white mb-1 truncate max-w-full">${file.name}</span>
            <span class="text-xs text-white/50">${(file.size / 1024).toFixed(0)} KB (PDF Wedding Card)</span>
          </div>
        `;
      } else {
        const previewUrl = URL.createObjectURL(file);
        innerHtml = `
          <div class="relative w-full rounded-xl overflow-hidden bg-black/60 flex items-center justify-center h-[320px] sm:h-[400px] border border-white/10 p-1.5 shadow-inner">
            <img src="${previewUrl}" class="w-full h-full object-contain rounded-lg shadow-lg" alt="Wedding Card" />
          </div>
          <div class="flex items-center justify-between px-2 pt-2 text-left">
            <div class="flex items-center gap-1.5 min-w-0">
              <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
              <span class="text-xs font-bold text-white truncate" title="${file.name}">${file.name}</span>
            </div>
            <span class="text-[10px] text-amber-300 font-mono shrink-0">${(file.size / 1024).toFixed(0)} KB</span>
          </div>
        `;
      }

      card.innerHTML = `
        <button type="button" class="btn-remove-thumb absolute top-3 right-3 w-6 h-6 rounded-full bg-red-600/90 text-white flex items-center justify-center text-xs hover:bg-red-500 transition shadow-lg z-10" title="Remove Card">
          <i class="fa-solid fa-xmark"></i>
        </button>
        ${innerHtml}
      `;

      card.addEventListener('click', () => openCardViewer(0));
      card.querySelector('.btn-remove-thumb').addEventListener('click', (ev) => {
        ev.stopPropagation();
        currentCardFiles.splice(0, 1);
        renderCardThumbnails();
      });

      cardThumbnailsGrid.appendChild(card);
      return;
    }

    // If multiple pages: Grid of cards with prominent height
    const gridDiv = document.createElement('div');
    gridDiv.className = 'grid grid-cols-2 gap-2.5';

    currentCardFiles.forEach((file, index) => {
      const card = document.createElement('div');
      card.className = 'relative rounded-xl overflow-hidden bg-black/40 border border-white/10 p-2 flex flex-col justify-between text-center group cursor-zoom-in hover:border-amber-400/40 transition';

      const isPdf = file.name.toLowerCase().endsWith('.pdf') || file.type.includes('pdf');
      let previewHtml = '';

      if (isPdf) {
        previewHtml = `
          <div class="w-full h-44 sm:h-56 rounded-lg bg-black/60 border border-white/10 flex flex-col items-center justify-center text-amber-300 mb-1.5 shadow">
            <i class="fa-solid fa-file-pdf text-2xl mb-1.5"></i>
            <span class="text-[10px] font-bold uppercase">PDF Page</span>
          </div>
        `;
      } else {
        const previewUrl = URL.createObjectURL(file);
        previewHtml = `
          <div class="relative w-full h-44 sm:h-56 rounded-lg overflow-hidden bg-black/60 mb-1.5 border border-white/10 flex items-center justify-center">
            <img src="${previewUrl}" class="w-full h-full object-contain rounded" />
          </div>
        `;
      }

      card.innerHTML = `
        <button type="button" class="btn-remove-thumb absolute top-1 right-1 w-4 h-4 rounded-full bg-red-600 text-white flex items-center justify-center text-[8px] hover:bg-red-500 transition shadow z-10" title="Remove">
          <i class="fa-solid fa-xmark"></i>
        </button>
        ${previewHtml}
        <div class="w-full px-0.5 text-left">
          <span class="text-[9px] font-bold text-white truncate block" title="${file.name}">
            P${index + 1}: ${file.name}
          </span>
          <span class="text-[8px] text-white/50 block">
            ${(file.size / 1024).toFixed(0)} KB
          </span>
        </div>
      `;

      card.addEventListener('click', () => openCardViewer(index));
      card.querySelector('.btn-remove-thumb').addEventListener('click', (ev) => {
        ev.stopPropagation();
        currentCardFiles.splice(index, 1);
        renderCardThumbnails();
      });

      gridDiv.appendChild(card);
    });

    cardThumbnailsGrid.appendChild(gridDiv);
    if (typeof updateFloatingCardView === 'function') updateFloatingCardView();
  }

  // Card Viewer Lightbox State & Logic
  const modalCardViewer = document.getElementById('modalCardViewer');
  const viewerCardTitle = document.getElementById('viewerCardTitle');
  const viewerCardBadge = document.getElementById('viewerCardBadge');
  const viewerImage = document.getElementById('viewerImage');
  const viewerPdfFrame = document.getElementById('viewerPdfFrame');
  const btnCloseViewer = document.getElementById('btnCloseViewer');
  const btnViewerZoomIn = document.getElementById('btnViewerZoomIn');
  const btnViewerZoomOut = document.getElementById('btnViewerZoomOut');
  const btnViewerReset = document.getElementById('btnViewerReset');
  const btnViewerPrev = document.getElementById('btnViewerPrev');
  const btnViewerNext = document.getElementById('btnViewerNext');
  const btnViewerOpenTab = document.getElementById('btnViewerOpenTab');
  const btnWatchAllCards = document.getElementById('btnWatchAllCards');
  const btnWatchCardStep2 = document.getElementById('btnWatchCardStep2');
  const viewerContainer = document.getElementById('viewerContainer');

  let viewerCurrentIndex = 0;
  let viewerZoom = 1.0;
  let viewerIsDragging = false;
  let viewerStartX = 0, viewerStartY = 0;
  let viewerTranslateX = 0, viewerTranslateY = 0;

  function updateViewerTransform() {
    if (viewerImage && !viewerImage.classList.contains('hidden')) {
      viewerImage.style.transform = `translate(${viewerTranslateX}px, ${viewerTranslateY}px) scale(${viewerZoom})`;
    }
  }

  function resetViewerZoom() {
    viewerZoom = 1.0;
    viewerTranslateX = 0;
    viewerTranslateY = 0;
    updateViewerTransform();
  }

  let touchSwipeStartX = 0;
  let touchSwipeStartY = 0;

  function openCardViewer(index = 0) {
    if (currentCardFiles.length === 0) {
      if (externalThumbnailUrl) {
        if (viewerCardTitle) viewerCardTitle.textContent = 'Scanned Card Preview';
        if (viewerCardBadge) viewerCardBadge.textContent = '1 / 1';
        resetViewerZoom();
        if (viewerPdfFrame) { viewerPdfFrame.classList.add('hidden'); viewerPdfFrame.src = ''; }
        if (viewerImage) {
          viewerImage.classList.remove('hidden');
          viewerImage.src = externalThumbnailUrl;
        }
        if (btnViewerPrev) btnViewerPrev.disabled = true;
        if (btnViewerNext) btnViewerNext.disabled = true;
        if (modalCardViewer) modalCardViewer.classList.remove('hidden');
        if (window.history && window.history.pushState) {
          window.history.pushState({ modal: 'cardViewer' }, '');
        }
        return;
      }
      showToast('No card file uploaded yet', 'info');
      return;
    }
    viewerCurrentIndex = Math.max(0, Math.min(index, currentCardFiles.length - 1));
    const file = currentCardFiles[viewerCurrentIndex];
    const isPdf = file.name.toLowerCase().endsWith('.pdf') || file.type.includes('pdf');

    if (viewerCardTitle) viewerCardTitle.textContent = file.name;
    if (viewerCardBadge) viewerCardBadge.textContent = `${viewerCurrentIndex + 1} / ${currentCardFiles.length}`;

    resetViewerZoom();

    if (isPdf) {
      if (viewerImage) viewerImage.classList.add('hidden');
      if (viewerPdfFrame) {
        viewerPdfFrame.classList.remove('hidden');
        viewerPdfFrame.src = URL.createObjectURL(file);
      }
      if (btnViewerZoomIn) btnViewerZoomIn.disabled = true;
      if (btnViewerZoomOut) btnViewerZoomOut.disabled = true;
      if (btnViewerReset) btnViewerReset.disabled = true;
    } else {
      if (viewerPdfFrame) {
        viewerPdfFrame.classList.add('hidden');
        viewerPdfFrame.src = '';
      }
      if (viewerImage) {
        viewerImage.classList.remove('hidden');
        viewerImage.src = URL.createObjectURL(file);
      }
      if (btnViewerZoomIn) btnViewerZoomIn.disabled = false;
      if (btnViewerZoomOut) btnViewerZoomOut.disabled = false;
      if (btnViewerReset) btnViewerReset.disabled = false;
    }

    if (btnViewerPrev) btnViewerPrev.disabled = viewerCurrentIndex === 0;
    if (btnViewerNext) btnViewerNext.disabled = viewerCurrentIndex === currentCardFiles.length - 1;

    if (modalCardViewer) modalCardViewer.classList.remove('hidden');
    if (window.history && window.history.pushState) {
      window.history.pushState({ modal: 'cardViewer' }, '');
    }
  }

  function closeCardViewer() {
    if (modalCardViewer) modalCardViewer.classList.add('hidden');
    if (viewerPdfFrame) viewerPdfFrame.src = '';
    if (viewerImage) viewerImage.src = '';
    resetViewerZoom();
  }

  if (btnCloseViewer) btnCloseViewer.addEventListener('click', closeCardViewer);
  if (btnWatchAllCards) btnWatchAllCards.addEventListener('click', () => openCardViewer(0));

  const btnHeaderWatchCard = document.getElementById('btnHeaderWatchCard');
  if (btnHeaderWatchCard) {
    btnHeaderWatchCard.addEventListener('click', () => {
      if (typeof openCardSidebar === 'function') {
        openCardSidebar();
      } else if (typeof openCardViewer === 'function') {
        openCardViewer(0);
      }
    });
  }

  if (btnViewerPrev) {
    btnViewerPrev.addEventListener('click', () => {
      if (viewerCurrentIndex > 0) openCardViewer(viewerCurrentIndex - 1);
    });
  }

  if (btnViewerNext) {
    btnViewerNext.addEventListener('click', () => {
      if (viewerCurrentIndex < currentCardFiles.length - 1) openCardViewer(viewerCurrentIndex + 1);
    });
  }

  if (btnViewerZoomIn) {
    btnViewerZoomIn.addEventListener('click', () => {
      viewerZoom = Math.min(4.0, viewerZoom + 0.25);
      updateViewerTransform();
    });
  }

  if (btnViewerZoomOut) {
    btnViewerZoomOut.addEventListener('click', () => {
      viewerZoom = Math.max(0.5, viewerZoom - 0.25);
      updateViewerTransform();
    });
  }

  if (btnViewerReset) btnViewerReset.addEventListener('click', resetViewerZoom);

  if (btnViewerOpenTab) {
    btnViewerOpenTab.addEventListener('click', () => {
      const file = currentCardFiles[viewerCurrentIndex];
      if (file) {
        const url = URL.createObjectURL(file);
        window.open(url, '_blank');
      } else if (externalThumbnailUrl) {
        window.open(externalThumbnailUrl, '_blank');
      }
    });
  }

  // Mobile Touch & Pointer Interaction for Fullscreen Card Viewer
  if (viewerImage) {
    viewerImage.addEventListener('dblclick', () => {
      if (viewerZoom > 1.0) {
        resetViewerZoom();
      } else {
        viewerZoom = 2.0;
        updateViewerTransform();
      }
    });

    // Mobile double-tap to toggle zoom
    let lastViewerTap = 0;
    viewerImage.addEventListener('touchend', (e) => {
      const now = Date.now();
      if (now - lastViewerTap < 320) {
        if (viewerZoom > 1.0) {
          resetViewerZoom();
        } else {
          viewerZoom = 2.0;
          updateViewerTransform();
        }
        lastViewerTap = 0;
      } else {
        lastViewerTap = now;
      }
    });

    // Touch & Mouse Pointer Pan / Swipe Handler
    viewerImage.addEventListener('pointerdown', (e) => {
      viewerStartX = e.clientX - viewerTranslateX;
      viewerStartY = e.clientY - viewerTranslateY;
      viewerIsDragging = true;
      touchSwipeStartX = e.clientX;
      touchSwipeStartY = e.clientY;
      try { viewerImage.setPointerCapture(e.pointerId); } catch (_) {}
    });

    viewerImage.addEventListener('pointermove', (e) => {
      if (!viewerIsDragging) return;
      if (viewerZoom > 1.0) {
        viewerTranslateX = e.clientX - viewerStartX;
        viewerTranslateY = e.clientY - viewerStartY;
        updateViewerTransform();
      }
    });

    const endViewerDrag = (e) => {
      if (!viewerIsDragging) return;
      viewerIsDragging = false;
      try { viewerImage.releasePointerCapture(e.pointerId); } catch (_) {}

      // If at 1.0x zoom on mobile, check for horizontal swipe to change pages
      if (viewerZoom <= 1.05 && touchSwipeStartX !== 0) {
        const diffX = e.clientX - touchSwipeStartX;
        const diffY = e.clientY - touchSwipeStartY;
        if (Math.abs(diffX) > 45 && Math.abs(diffX) > Math.abs(diffY)) {
          if (diffX < -45 && viewerCurrentIndex < currentCardFiles.length - 1) {
            openCardViewer(viewerCurrentIndex + 1); // Swipe left -> Next
          } else if (diffX > 45 && viewerCurrentIndex > 0) {
            openCardViewer(viewerCurrentIndex - 1); // Swipe right -> Prev
          }
        }
      }
      touchSwipeStartX = 0;
      touchSwipeStartY = 0;
    };

    viewerImage.addEventListener('pointerup', endViewerDrag);
    viewerImage.addEventListener('pointercancel', endViewerDrag);
  }

  // Wheel zoom
  if (viewerContainer) {
    viewerContainer.addEventListener('wheel', (e) => {
      if (viewerImage && !viewerImage.classList.contains('hidden')) {
        e.preventDefault();
        const delta = e.deltaY < 0 ? 0.2 : -0.2;
        viewerZoom = Math.max(0.5, Math.min(4.0, viewerZoom + delta));
        updateViewerTransform();
      }
    }, { passive: false });
  }

  // Keyboard navigation
  window.addEventListener('keydown', (e) => {
    if (modalCardViewer && !modalCardViewer.classList.contains('hidden')) {
      if (e.key === 'Escape') closeCardViewer();
      else if (e.key === 'ArrowLeft' && viewerCurrentIndex > 0) openCardViewer(viewerCurrentIndex - 1);
      else if (e.key === 'ArrowRight' && viewerCurrentIndex < currentCardFiles.length - 1) openCardViewer(viewerCurrentIndex + 1);
    }
  });

  // ==================== SMART MOBILE CARD SIDEBAR CONTROLLER ====================
  const cardSidebarPanel = document.getElementById('cardSidebarPanel');
  const cardSidebarBackdrop = document.getElementById('cardSidebarBackdrop');
  const cardSidebarEdgeTab = document.getElementById('cardSidebarEdgeTab');
  const btnCollapseCardSidebar = document.getElementById('btnCollapseCardSidebar');
  const btnCloseSidebarBottom = document.getElementById('btnCloseSidebarBottom');

  // Backwards-compatible aliases
  const floatingCardWidget = cardSidebarPanel;
  const floatingLauncherPill = cardSidebarEdgeTab;

  const floatingCardBody = document.getElementById('floatingCardBody');
  const floatingCardImg = document.getElementById('floatingCardImg');
  const floatingCardEmptyState = document.getElementById('floatingCardEmptyState');
  const floatingPageBadge = document.getElementById('floatingPageBadge');
  const floatingZoomVal = document.getElementById('floatingZoomVal');
  const floatingZoomPill = document.getElementById('floatingZoomPill');

  const btnFloatingZoomIn = document.getElementById('btnFloatingZoomIn');
  const btnFloatingZoomOut = document.getElementById('btnFloatingZoomOut');
  const btnFloatingResetZoom = document.getElementById('btnFloatingResetZoom');
  const btnFloatingExpandFull = document.getElementById('btnFloatingExpandFull');
  const btnFloatingPrevPage = document.getElementById('btnFloatingPrevPage');
  const btnFloatingNextPage = document.getElementById('btnFloatingNextPage');
  const btnToggleFloatingInDetails = document.getElementById('btnToggleFloatingInDetails');

  let floatingCurrentPageIndex = 0;
  let floatingZoom = 1.0;
  let floatingPanX = 0;
  let floatingPanY = 0;
  let floatingIsPanning = false;
  let floatingPanStartX = 0;
  let floatingPanStartY = 0;
  let isSidebarOpen = false;
  let externalThumbnailUrl = ''; // Fallback image when loaded from history

  function updateFloatingCardView() {
    if (!floatingCardImg) return;

    if (currentCardFiles.length > 0) {
      floatingCurrentPageIndex = Math.max(0, Math.min(floatingCurrentPageIndex, currentCardFiles.length - 1));
      const file = currentCardFiles[floatingCurrentPageIndex];
      const isPdf = file.name.toLowerCase().endsWith('.pdf') || file.type.includes('pdf');

      if (isPdf) {
        floatingCardImg.classList.add('hidden');
        if (floatingCardEmptyState) {
          floatingCardEmptyState.classList.remove('hidden');
          floatingCardEmptyState.innerHTML = '<i class="fa-solid fa-file-pdf text-3xl text-amber-400 mb-1.5"></i><span class="text-xs font-bold text-white">PDF Card Page</span>';
        }
      } else {
        const objUrl = URL.createObjectURL(file);
        floatingCardImg.src = objUrl;
        floatingCardImg.classList.remove('hidden');
        if (floatingCardEmptyState) floatingCardEmptyState.classList.add('hidden');
      }

      if (floatingPageBadge) {
        floatingPageBadge.textContent = `Page ${floatingCurrentPageIndex + 1}/${currentCardFiles.length}`;
      }
      if (btnFloatingPrevPage && btnFloatingNextPage) {
        if (currentCardFiles.length > 1) {
          btnFloatingPrevPage.classList.remove('hidden');
          btnFloatingNextPage.classList.remove('hidden');
          btnFloatingPrevPage.disabled = (floatingCurrentPageIndex <= 0);
          btnFloatingNextPage.disabled = (floatingCurrentPageIndex >= currentCardFiles.length - 1);
        } else {
          btnFloatingPrevPage.classList.add('hidden');
          btnFloatingNextPage.classList.add('hidden');
        }
      }
    } else if (externalThumbnailUrl) {
      floatingCardImg.src = externalThumbnailUrl;
      floatingCardImg.classList.remove('hidden');
      if (floatingCardEmptyState) floatingCardEmptyState.classList.add('hidden');
      if (floatingPageBadge) floatingPageBadge.textContent = 'Page 1/1';
      if (btnFloatingPrevPage) btnFloatingPrevPage.classList.add('hidden');
      if (btnFloatingNextPage) btnFloatingNextPage.classList.add('hidden');
    } else {
      floatingCardImg.classList.add('hidden');
      if (floatingCardEmptyState) {
        floatingCardEmptyState.classList.remove('hidden');
        floatingCardEmptyState.innerHTML = '<i class="fa-solid fa-image text-3xl text-amber-400/40 mb-1.5"></i><span class="text-xs">No Card</span>';
      }
      if (floatingPageBadge) floatingPageBadge.textContent = '0/0';
      if (btnFloatingPrevPage) btnFloatingPrevPage.classList.add('hidden');
      if (btnFloatingNextPage) btnFloatingNextPage.classList.add('hidden');
    }
  }

  function updateFloatingTransform() {
    if (!floatingCardImg) return;
    floatingCardImg.style.transform = `translate(${floatingPanX}px, ${floatingPanY}px) scale(${floatingZoom})`;
    if (floatingZoomVal) {
      floatingZoomVal.textContent = `${Math.round(floatingZoom * 100)}%`;
    }
    if (floatingZoomPill) {
      floatingZoomPill.style.opacity = (floatingZoom === 1.0) ? '0.5' : '1.0';
    }
  }

  function resetFloatingZoom() {
    floatingZoom = 1.0;
    floatingPanX = 0;
    floatingPanY = 0;
    updateFloatingTransform();
  }

  function openCardSidebar() {
    if (!cardSidebarPanel) return;
    isSidebarOpen = true;
    updateFloatingCardView();

    // Show backdrop with fade
    if (cardSidebarBackdrop) {
      cardSidebarBackdrop.classList.remove('hidden');
      requestAnimationFrame(() => {
        cardSidebarBackdrop.style.opacity = '1';
        cardSidebarBackdrop.style.pointerEvents = 'auto';
      });
    }

    // Slide in drawer panel
    cardSidebarPanel.classList.remove('translate-x-full');
    cardSidebarPanel.classList.add('translate-x-0');

    // Hide edge tab while drawer is visible
    if (cardSidebarEdgeTab) cardSidebarEdgeTab.classList.add('opacity-0', 'pointer-events-none');
  }

  function closeCardSidebar() {
    if (!cardSidebarPanel) return;
    isSidebarOpen = false;

    // Slide out drawer panel
    cardSidebarPanel.classList.remove('translate-x-0');
    cardSidebarPanel.classList.add('translate-x-full');

    // Fade out backdrop
    if (cardSidebarBackdrop) {
      cardSidebarBackdrop.style.opacity = '0';
      cardSidebarBackdrop.style.pointerEvents = 'none';
      setTimeout(() => {
        if (!isSidebarOpen) cardSidebarBackdrop.classList.add('hidden');
      }, 300);
    }

    updateSidebarEdgeTabVisibility();
  }

  function toggleCardSidebar() {
    if (isSidebarOpen) {
      closeCardSidebar();
    } else {
      openCardSidebar();
    }
  }

  // Aliases for backwards compatibility
  function openFloatingWidget() { openCardSidebar(); }
  function closeFloatingWidget() { closeCardSidebar(); }
  function toggleFloatingWidget() { toggleCardSidebar(); }

  function updateSidebarEdgeTabVisibility() {
    if (!cardSidebarEdgeTab) return;
    const hasCard = (currentCardFiles && currentCardFiles.length > 0) || Boolean(externalThumbnailUrl);

    // Toggle active green indicator dot on edge tab
    const dotPing = document.getElementById('cardSidebarActiveDot');
    const dotStatic = document.getElementById('cardSidebarActiveDotStatic');
    if (dotPing && dotStatic) {
      if (hasCard) {
        dotPing.classList.remove('hidden');
        dotStatic.classList.remove('hidden');
      } else {
        dotPing.classList.add('hidden');
        dotStatic.classList.add('hidden');
      }
    }

    if (!isSidebarOpen) {
      cardSidebarEdgeTab.classList.remove('hidden', 'opacity-0', 'pointer-events-none');
    } else {
      cardSidebarEdgeTab.classList.add('opacity-0', 'pointer-events-none');
    }
  }

  const btnSidebarUploadCard = document.getElementById('btnSidebarUploadCard');
  if (btnSidebarUploadCard) {
    btnSidebarUploadCard.addEventListener('click', () => {
      closeCardSidebar();
      const cardFileInput = document.getElementById('cardFileInput');
      if (cardFileInput) cardFileInput.click();
    });
  }

  // Make Edge Tab vertically draggable so editor can position it anywhere along edge
  if (cardSidebarEdgeTab) {
    let isDraggingTab = false;
    let tabStartY = 0;
    let initialTabTop = 0;
    let movedTab = false;

    cardSidebarEdgeTab.addEventListener('pointerdown', (e) => {
      isDraggingTab = true;
      movedTab = false;
      tabStartY = e.clientY;
      const rect = cardSidebarEdgeTab.getBoundingClientRect();
      initialTabTop = rect.top;
      try { cardSidebarEdgeTab.setPointerCapture(e.pointerId); } catch (_) {}
    });

    cardSidebarEdgeTab.addEventListener('pointermove', (e) => {
      if (!isDraggingTab) return;
      const dy = e.clientY - tabStartY;
      if (Math.abs(dy) > 5) movedTab = true;
      if (movedTab) {
        const newY = Math.max(70, Math.min(window.innerHeight - 80, initialTabTop + dy));
        cardSidebarEdgeTab.style.top = `${newY}px`;
        cardSidebarEdgeTab.style.transform = 'none';
      }
    });

    const endTabDrag = (e) => {
      if (!isDraggingTab) return;
      isDraggingTab = false;
      try { cardSidebarEdgeTab.releasePointerCapture(e.pointerId); } catch (_) {}
      if (!movedTab) {
        openCardSidebar();
      }
    };
    cardSidebarEdgeTab.addEventListener('pointerup', endTabDrag);
    cardSidebarEdgeTab.addEventListener('pointercancel', endTabDrag);
  }

  // Swipe right on sidebar drawer to close
  if (cardSidebarPanel) {
    let touchStartX = 0;
    let touchStartY = 0;
    cardSidebarPanel.addEventListener('touchstart', (e) => {
      touchStartX = e.touches[0].clientX;
      touchStartY = e.touches[0].clientY;
    }, { passive: true });

    cardSidebarPanel.addEventListener('touchend', (e) => {
      const diffX = e.changedTouches[0].clientX - touchStartX;
      const diffY = Math.abs(e.changedTouches[0].clientY - touchStartY);
      if (diffX > 60 && diffX > diffY) {
        closeCardSidebar();
      }
    }, { passive: true });
  }

  // Touch Pan, Double-Tap & Pinch-to-Zoom on image
  if (floatingCardBody) {
    let initialPinchDist = 0;
    let initialZoom = 1.0;
    let lastTapTime = 0;

    floatingCardBody.addEventListener('touchstart', (e) => {
      if (e.touches.length === 2) {
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        initialPinchDist = Math.hypot(dx, dy);
        initialZoom = floatingZoom;
      } else if (e.touches.length === 1) {
        const now = Date.now();
        if (now - lastTapTime < 320) {
          if (floatingZoom > 1.2) {
            resetFloatingZoom();
          } else {
            floatingZoom = 2.2;
            updateFloatingTransform();
          }
          lastTapTime = 0;
        } else {
          lastTapTime = now;
        }

        floatingIsPanning = true;
        floatingPanStartX = e.touches[0].clientX - floatingPanX;
        floatingPanStartY = e.touches[0].clientY - floatingPanY;
      }
    }, { passive: true });

    floatingCardBody.addEventListener('touchmove', (e) => {
      if (e.touches.length === 2 && initialPinchDist > 0) {
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        const dist = Math.hypot(dx, dy);
        const scale = dist / initialPinchDist;
        floatingZoom = Math.max(0.7, Math.min(4.5, initialZoom * scale));
        updateFloatingTransform();
      } else if (e.touches.length === 1 && floatingIsPanning) {
        floatingPanX = e.touches[0].clientX - floatingPanStartX;
        floatingPanY = e.touches[0].clientY - floatingPanStartY;
        updateFloatingTransform();
      }
    }, { passive: true });

    floatingCardBody.addEventListener('touchend', (e) => {
      if (e.touches.length < 2) initialPinchDist = 0;
      if (e.touches.length === 0) floatingIsPanning = false;
    }, { passive: true });

    // Pointer drag for mouse
    floatingCardBody.addEventListener('pointerdown', (e) => {
      if (e.target.closest('button')) return;
      floatingIsPanning = true;
      floatingPanStartX = e.clientX - floatingPanX;
      floatingPanStartY = e.clientY - floatingPanY;
      try { floatingCardBody.setPointerCapture(e.pointerId); } catch (_) {}
    });

    floatingCardBody.addEventListener('pointermove', (e) => {
      if (!floatingIsPanning) return;
      floatingPanX = e.clientX - floatingPanStartX;
      floatingPanY = e.clientY - floatingPanStartY;
      updateFloatingTransform();
    });

    const endPointerPan = (e) => {
      if (floatingIsPanning) {
        floatingIsPanning = false;
        try { floatingCardBody.releasePointerCapture(e.pointerId); } catch (_) {}
      }
    };
    floatingCardBody.addEventListener('pointerup', endPointerPan);
    floatingCardBody.addEventListener('pointercancel', endPointerPan);

    floatingCardBody.addEventListener('wheel', (e) => {
      e.preventDefault();
      const delta = e.deltaY < 0 ? 0.25 : -0.25;
      floatingZoom = Math.max(0.6, Math.min(4.5, floatingZoom + delta));
      updateFloatingTransform();
    }, { passive: false });
  }

  // Sidebar Button Listeners
  if (btnCollapseCardSidebar) btnCollapseCardSidebar.addEventListener('click', closeCardSidebar);
  if (btnCloseSidebarBottom) btnCloseSidebarBottom.addEventListener('click', closeCardSidebar);
  if (cardSidebarBackdrop) cardSidebarBackdrop.addEventListener('click', closeCardSidebar);

  if (btnToggleFloatingInDetails) {
    btnToggleFloatingInDetails.addEventListener('click', () => {
      if (currentCardFiles.length > 0 || Boolean(externalThumbnailUrl)) {
        openCardSidebar();
      } else {
        showToast('No card photo uploaded yet (Upload in Step 1)', 'info');
      }
    });
  }


  if (btnFloatingZoomIn) {
    btnFloatingZoomIn.addEventListener('click', () => {
      floatingZoom = Math.min(4.5, floatingZoom + 0.35);
      updateFloatingTransform();
    });
  }

  if (btnFloatingZoomOut) {
    btnFloatingZoomOut.addEventListener('click', () => {
      floatingZoom = Math.max(0.6, floatingZoom - 0.35);
      updateFloatingTransform();
    });
  }

  if (btnFloatingResetZoom) {
    btnFloatingResetZoom.addEventListener('click', resetFloatingZoom);
  }

  if (btnFloatingExpandFull) {
    btnFloatingExpandFull.addEventListener('click', () => {
      closeCardSidebar();
      openCardViewer(floatingCurrentPageIndex);
    });
  }

  if (btnFloatingPrevPage) {
    btnFloatingPrevPage.addEventListener('click', () => {
      if (floatingCurrentPageIndex > 0) {
        floatingCurrentPageIndex--;
        resetFloatingZoom();
        updateFloatingCardView();
      }
    });
  }

  if (btnFloatingNextPage) {
    btnFloatingNextPage.addEventListener('click', () => {
      if (floatingCurrentPageIndex < currentCardFiles.length - 1) {
        floatingCurrentPageIndex++;
        resetFloatingZoom();
        updateFloatingCardView();
      }
    });
  }

  // File Upload Handlers
  cardFileInput.addEventListener('change', (e) => {
    const selected = Array.from(e.target.files);
    if (selected.length > 0) {
      currentCardFiles = [...currentCardFiles, ...selected];
      renderCardThumbnails();
    }
  });

  if (btnAddMoreCards) {
    btnAddMoreCards.addEventListener('click', (e) => {
      e.stopPropagation();
      cardFileInput.click();
    });
  }

  // Fast client-side image compression so mobile devices upload in 0.05s instead of 10s!
  function compressImageForScan(file, maxDim = 1500, quality = 0.8) {
    return new Promise((resolve) => {
      if (!file || file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
        return resolve(file);
      }
      const img = new Image();
      const url = URL.createObjectURL(file);
      img.onload = () => {
        URL.revokeObjectURL(url);
        let w = img.width;
        let h = img.height;
        if (w > maxDim || h > maxDim) {
          const scale = maxDim / Math.max(w, h);
          w = Math.round(w * scale);
          h = Math.round(h * scale);
        }
        const canvas = document.createElement('canvas');
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, w, h);
        canvas.toBlob((blob) => {
          if (blob && blob.size < file.size) {
            const compressed = new File([blob], file.name.replace(/\.[^.]+$/, '.jpg'), { type: 'image/jpeg' });
            resolve(compressed);
          } else {
            resolve(file);
          }
        }, 'image/jpeg', quality);
      };
      img.onerror = () => resolve(file);
      img.src = url;
    });
  }

  // AI Scan Action (Ultra-Fast 1-Pass Scanning)
  btnStartAiScan.addEventListener('click', async () => {
    if (currentCardFiles.length === 0) {
      showToast('Please upload a wedding card photo or PDF first!', 'error');
      return;
    }

    const apiKey = localStorage.getItem('gemini_api_key') || '';
    const numFiles = currentCardFiles.length;

    showLoading(true, 'AI Scanning Card...', `Extracting details from ${numFiles} page(s) in seconds...`);

    try {
      // 1. Parallel client-side compression (cuts upload payload from 10MB to ~200KB)
      const readyFiles = await Promise.all(currentCardFiles.map(f => compressImageForScan(f)));

      const formData = new FormData();
      readyFiles.forEach(f => {
        formData.append('files', f);
      });
      formData.append('api_key', apiKey);

      const resp = await authFetch('/api/scan', {
        method: 'POST',
        body: formData
      });
      const res = await resp.json();
      showLoading(false);

      if (res.success && res.data) {
        weddingData = res.data;
        populateForm(weddingData);

        // 1. Show simple, clean "Success!" notification
        showToast('✅ Success! Card Scanned Successfully', 'success', 2500);

        // 2. Automatically navigate to Step 2 (Details page) after 1 second without auto-opening float card
        setTimeout(() => {
          showStep(2);
          closeFloatingWidget();
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }, 1000);
      } else {
        showToast('Scan error: ' + (res.error || 'Failed to extract'), 'error');
      }
    } catch (err) {
      showLoading(false);
      showToast('Server connection failed: ' + err.message, 'error');
    }
  });

  // Demo Data Test Action
  btnLoadDemo.addEventListener('click', async () => {
    showLoading(true, 'Loading Sample Data...', 'Preparing demonstration wedding card data...');
    try {
      const resp = await authFetch('/api/demo-data');
      const data = await resp.json();
      weddingData = data;
      populateForm(weddingData);
      showLoading(false);
      showStep(2);
      closeFloatingWidget();
      showToast('Sample demo data loaded successfully!', 'success');
    } catch (err) {
      showLoading(false);
      showToast('Failed to load demo: ' + err.message, 'error');
    }
  });

  // Form Population
  function populateForm(data) {
    if (data.card_side) {
      setCardSide(data.card_side);
    } else {
      setCardSide('groom');
    }

    document.getElementById('inpPariwar').value = data.pariwar_name || '';

    document.getElementById('inpGroomName').value = data.groom_name || '';
    document.getElementById('inpBrideName').value = data.bride_name || '';

    if (document.getElementById('inpGroomGrandparents')) {
      document.getElementById('inpGroomGrandparents').value = data.groom_grandparents || '';
    }
    document.getElementById('inpGroomFather').value = data.groom_father || '';
    document.getElementById('inpGroomMother').value = data.groom_mother || '';
    document.getElementById('inpGroomVillage').value = data.groom_village || '';
    document.getElementById('inpGroomDistrict').value = data.groom_district || '';

    if (document.getElementById('inpBrideGrandparents')) {
      document.getElementById('inpBrideGrandparents').value = data.bride_grandparents || '';
    }
    document.getElementById('inpBrideFather').value = data.bride_father || '';
    document.getElementById('inpBrideMother').value = data.bride_mother || '';
    document.getElementById('inpBrideVillage').value = data.bride_village || '';
    document.getElementById('inpBrideDistrict').value = data.bride_district || '';

    // Events with editable titles (NO Time)
    if (document.getElementById('inpEv1Title')) {
      document.getElementById('inpEv1Title').value = data.event1_title || 'हल्दी, मंडप';
    }
    document.getElementById('inpEv1Date').value = data.event1_date || '10.07.2026';
    document.getElementById('inpEv1Day').value = data.event1_day || 'मंगलवार';

    if (document.getElementById('inpEv2Title')) {
      document.getElementById('inpEv2Title').value = data.event2_title || 'तेल, मायन';
    }
    document.getElementById('inpEv2Date').value = data.event2_date || '11.07.2026';
    document.getElementById('inpEv2Day').value = data.event2_day || 'बुधवार';

    if (document.getElementById('inpEv3Title')) {
      document.getElementById('inpEv3Title').value = data.event3_title || 'मंडप';
    }
    document.getElementById('inpEv3Date').value = data.event3_date || '10.07.2026';
    document.getElementById('inpEv3Day').value = data.event3_day || 'मंगलवार';

    if (document.getElementById('inpEv4Title')) {
      const defaultEv4 = (data.card_side === 'bride') ? 'बारात स्वागत व शुभ विवाह' : 'बारात प्रस्थान';
      document.getElementById('inpEv4Title').value = data.event4_title || defaultEv4;
    }
    document.getElementById('inpEv4Date').value = data.event4_date || '11.07.2026';
    document.getElementById('inpEv4Day').value = data.event4_day || 'बुधवार';

    document.getElementById('inpVenueGram').value = data.venue_gram || '';
    document.getElementById('inpVenueDistrict').value = data.venue_district || '';

    document.getElementById('inpVinit').value = data.vinit_names || 'श्री लखन (पापा)\nश्रीमती लता बाई (माँ)';
    document.getElementById('inpStudioName').value = 'Amar Edit';
    document.getElementById('inpStudioPhone').value = '7067392032';

    // Update Header with Groom or Bride Project Name
    updateHeaderProjectName();
  }

  // Real-time Header update when user types names
  ['inpGroomName', 'inpBrideName', 'inpPariwar'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', updateHeaderProjectName);
  });

  // Gather Form Data
  function getFormData() {
    return {
      card_side: currentCardSide,
      pariwar_name: document.getElementById('inpPariwar').value || 'साहू परिवार',
      groom_name: document.getElementById('inpGroomName').value || 'राम',
      bride_name: document.getElementById('inpBrideName').value || 'नेहा',

      groom_father: document.getElementById('inpGroomFather').value || 'श्री मनोहर लाल',
      groom_mother: document.getElementById('inpGroomMother').value || 'श्रीमती कमला बाई',
      groom_grandparents: document.getElementById('inpGroomGrandparents') ? document.getElementById('inpGroomGrandparents').value : '',
      groom_village: document.getElementById('inpGroomVillage').value || 'डोंगरगढ़',
      groom_district: document.getElementById('inpGroomDistrict').value || 'राजनांदगांव',
      groom_state: 'छत्तीसगढ़',

      bride_father: document.getElementById('inpBrideFather').value || 'श्री रमेश कुमार',
      bride_mother: document.getElementById('inpBrideMother').value || 'श्रीमती गीता बाई',
      bride_grandparents: document.getElementById('inpBrideGrandparents') ? document.getElementById('inpBrideGrandparents').value : '',
      bride_village: document.getElementById('inpBrideVillage').value || 'खैरागढ़',
      bride_district: document.getElementById('inpBrideDistrict').value || 'राजनांदगांव',
      bride_state: 'छत्तीसगढ़',

      event1_title: document.getElementById('inpEv1Title') ? document.getElementById('inpEv1Title').value || 'हल्दी, मंडप' : 'हल्दी, मंडप',
      event1_date: document.getElementById('inpEv1Date').value || '10.07.2026',
      event1_day: document.getElementById('inpEv1Day').value || 'मंगलवार',

      event2_title: document.getElementById('inpEv2Title') ? document.getElementById('inpEv2Title').value || 'तेल, मायन' : 'तेल, मायन',
      event2_date: document.getElementById('inpEv2Date').value || '11.07.2026',
      event2_day: document.getElementById('inpEv2Day').value || 'बुधवार',

      event3_title: document.getElementById('inpEv3Title') ? document.getElementById('inpEv3Title').value || 'मंडप' : 'मंडप',
      event3_date: document.getElementById('inpEv3Date').value || '10.07.2026',
      event3_day: document.getElementById('inpEv3Day').value || 'मंगलवार',

      event4_title: document.getElementById('inpEv4Title') ? document.getElementById('inpEv4Title').value || 'बारात प्रस्थान' : 'बारात प्रस्थान',
      event4_date: document.getElementById('inpEv4Date').value || '11.07.2026',
      event4_day: document.getElementById('inpEv4Day').value || 'बुधवार',

      venue_gram: document.getElementById('inpVenueGram').value || 'जंगलपुर',
      venue_district: document.getElementById('inpVenueDistrict').value || 'राजनांदगांव',

      vinit_names: document.getElementById('inpVinit').value || 'श्री लखन (पापा)\nश्रीमती लता बाई (माँ)',
      studio_name: 'Amar Edit',
      studio_phone: '7067392032'
    };
  }

  // Render Summary Card in Step 3
  function renderSummaryCard(data) {
    const isBride = data.card_side === 'bride';

    // Pariwar & Side
    const elPariwar = document.getElementById('previewCardPariwar');
    if (elPariwar) elPariwar.textContent = data.pariwar_name || 'साहू परिवार';

    const elBadge = document.getElementById('previewCardSideBadge');
    if (elBadge) {
      elBadge.className = isBride
        ? 'text-[10px] bg-pink-500/20 text-pink-300 border border-pink-500/40 px-2.5 py-0.5 rounded-full font-bold'
        : 'text-[10px] bg-blue-500/20 text-blue-300 border border-blue-500/40 px-2.5 py-0.5 rounded-full font-bold';
      elBadge.textContent = isBride ? 'वधू पक्ष' : 'वर पक्ष';
    }

    // Headline couple names
    const elHeadline = document.getElementById('previewCoupleHeadline');
    if (elHeadline) {
      if (isBride) {
        elHeadline.innerHTML = `${data.bride_name || 'Bride'} <span class="text-xs text-rose-300 font-normal">&</span> ${data.groom_name || 'Groom'}`;
      } else {
        elHeadline.innerHTML = `${data.groom_name || 'Groom'} <span class="text-xs text-rose-300 font-normal">&</span> ${data.bride_name || 'Bride'}`;
      }
    }

    // Groom side details
    const elGgp = document.getElementById('previewGroomGrandparents');
    if (elGgp) elGgp.textContent = data.groom_grandparents ? data.groom_grandparents : '';

    const elGp = document.getElementById('previewGroomParents');
    if (elGp) {
      const p1 = data.groom_father || '';
      const p2 = data.groom_mother ? `\n${data.groom_mother}` : '';
      elGp.textContent = `${p1}${p2}`.trim();
    }

    const elGpl = document.getElementById('previewGroomPlace');
    if (elGpl) {
      const d = data.groom_district || '';
      const parts = [data.groom_village || '', d].filter(Boolean);
      elGpl.textContent = parts.join(', ');
    }

    // Bride side details
    const elBgp = document.getElementById('previewBrideGrandparents');
    if (elBgp) elBgp.textContent = data.bride_grandparents ? data.bride_grandparents : '';

    const elBp = document.getElementById('previewBrideParents');
    if (elBp) {
      const p1 = data.bride_father || '';
      const p2 = data.bride_mother ? `\n${data.bride_mother}` : '';
      elBp.textContent = `${p1}${p2}`.trim();
    }

    const elBpl = document.getElementById('previewBridePlace');
    if (elBpl) {
      const d = data.bride_district || '';
      const parts = [data.bride_village || '', d].filter(Boolean);
      elBpl.textContent = parts.join(', ');
    }

    // Events list (No Time)
    const elEvList = document.getElementById('previewEventsList');
    if (elEvList) {
      const evs = [
        { t: data.event1_title, d: data.event1_date, dy: data.event1_day },
        { t: data.event2_title, d: data.event2_date, dy: data.event2_day },
        { t: data.event3_title, d: data.event3_date, dy: data.event3_day },
        { t: data.event4_title, d: data.event4_date, dy: data.event4_day }
      ].filter(e => e.t || e.d);

      elEvList.innerHTML = evs.map((ev, i) => `
        <div class="p-2 rounded-lg bg-black/40 border border-white/10 flex items-center justify-between">
          <div>
            <span class="text-amber-300 font-bold text-xs block">${i + 1}. ${ev.t || 'Ceremony'}</span>
            <span class="text-[10px] text-white font-medium">${ev.dy ? ev.dy + ', ' : ''}${ev.d || ''}</span>
          </div>
        </div>
      `).join('');
    }

    // Venue & Vinit
    const elVenue = document.getElementById('previewVenue');
    if (elVenue) {
      const vparts = [data.venue_gram, data.venue_district].filter(Boolean);
      elVenue.textContent = vparts.join(', ') || 'Venue';
    }

    const elVinit = document.getElementById('previewVinit');
    if (elVinit) {
      const vinitFirst = (data.vinit_names || '').split('\n').filter(Boolean)[0] || 'Family Elders';
      elVinit.textContent = vinitFirst;
    }
  }

  // Project Generation Helper (.amzip or .xml)
  async function generateProjectPackage(exportFormat = 'auto') {
    const data = getFormData();
    const fontMode = document.querySelector('input[name="fontMode"]:checked')?.value || 'hybrid';
    const templateName = document.getElementById('selectTemplate').value;

    const bodyData = new FormData();
    bodyData.append('data', JSON.stringify(data));
    bodyData.append('font_mode', fontMode);
    bodyData.append('template_name', templateName);
    bodyData.append('export_format', exportFormat);
    bodyData.append('editor_id', getCurrentEditorId());

    if (groomPhotoFile) {
      bodyData.append('groom_photo', groomPhotoFile);
    }
    if (bridePhotoFile) {
      bodyData.append('bride_photo', bridePhotoFile);
    }

    const resp = await authFetch('/api/generate', {
      method: 'POST',
      body: bodyData
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.error || 'Project generation failed');
    }

    const blob = await resp.blob();
    let filename = '';
    const disp = resp.headers.get('content-disposition');
    if (disp) {
      const matchUtf8 = disp.match(/filename\*=UTF-8''([^;]+)/i);
      if (matchUtf8 && matchUtf8[1]) {
        filename = decodeURIComponent(matchUtf8[1]);
      } else {
        const matchPlain = disp.match(/filename="?([^";]+)"?/i);
        if (matchPlain && matchPlain[1]) {
          filename = matchPlain[1];
        }
      }
    }

    if (!filename) {
      const primaryName = (data.card_side === 'bride' ? data.bride_name : data.groom_name) || 'Vivah';
      const isZip = (exportFormat === 'amzip') || (exportFormat === 'auto' && (groomPhotoFile || bridePhotoFile));
      filename = `${primaryName}.${isZip ? 'amzip' : 'xml'}`;
    }

    return { blob, filename, data, isAmzip: filename.endsWith('.amzip') };
  }

  function triggerDownload(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  }

  // Proceed button from Step 2
  btnProceedToXml.addEventListener('click', () => {
    const data = getFormData();
    renderSummaryCard(data);
    showStep(3);
  });

  // Helper: Guide modal for opening XML in After Motion Z without Play Store redirection
  const modalAfterMotionGuide = document.getElementById('modalAfterMotionGuide');
  const guideFilenameText = document.getElementById('guideFilenameText');

  window.openAfterMotionGuideModal = function(filename = '') {
    if (guideFilenameText && filename) {
      guideFilenameText.textContent = filename + ' downloaded successfully!';
    }
    if (modalAfterMotionGuide) {
      modalAfterMotionGuide.classList.remove('hidden');
      if (window.history && window.history.pushState) {
        window.history.pushState({ modal: 'afterMotionGuide' }, '');
      }
    }
  };

  window.closeAfterMotionGuideModal = function() {
    if (modalAfterMotionGuide) {
      modalAfterMotionGuide.classList.add('hidden');
    }
  };

  if (modalAfterMotionGuide) {
    modalAfterMotionGuide.addEventListener('click', (e) => {
      if (e.target === modalAfterMotionGuide) window.closeAfterMotionGuideModal();
    });
  }

  // 1. Direct Share XML to After Motion Z (Web Share API with smart fallback)
  if (btnShareAfterMotion) {
    btnShareAfterMotion.addEventListener('click', async () => {
      showLoading(true, 'Sharing XML Project...', 'Compiling wedding project XML for After Motion Z...');
      try {
        const { blob, filename, isAmzip } = await generateProjectPackage('xml');
        const mimeType = isAmzip ? 'application/zip' : 'application/xml';
        const file = new File([blob], filename, { type: mimeType });

        // If Web Share API supports file sharing (Mobile Android / HTTPS context)
        if (navigator.canShare && navigator.canShare({ files: [file] })) {
          showLoading(false);
          await navigator.share({
            files: [file],
            title: filename,
            text: 'Open with After Motion Z / Alight Motion'
          });
          showToast('Share drawer opened! Select After Motion Z.', 'success');
        } else {
          // Clean Download + Guide (NO Play Store redirect)
          triggerDownload(blob, filename);
          showLoading(false);
          showToast(`✅ ${filename} downloaded successfully!`, 'success');
          setTimeout(() => window.openAfterMotionGuideModal(filename), 350);
        }
      } catch (err) {
        showLoading(false);
        if (err.name !== 'AbortError') {
          try {
            const { blob, filename } = await generateProjectPackage('xml');
            triggerDownload(blob, filename);
            showToast(`✅ ${filename} downloaded successfully!`, 'success');
            setTimeout(() => window.openAfterMotionGuideModal(filename), 350);
          } catch (_) {}
        }
      }
    });
  }

  // 2. Direct Open / Guide to After Motion Z (Never force Play Store)
  const btnRedirectAfterMotion = document.getElementById('btnRedirectAfterMotion');
  if (btnRedirectAfterMotion) {
    btnRedirectAfterMotion.addEventListener('click', async () => {
      showLoading(true, 'Opening After Motion Z...', 'Downloading project and preparing import guide...');
      try {
        const { blob, filename } = await generateProjectPackage('xml');
        triggerDownload(blob, filename);
        showLoading(false);
        showToast(`🚀 ${filename} downloaded successfully!`, 'success');
        setTimeout(() => {
          window.openAfterMotionGuideModal(filename);
        }, 350);
      } catch (err) {
        showLoading(false);
        showToast('Download error: ' + err.message, 'error');
      }
    });
  }

  // Manual Download .amzip Action (Package with photos)
  if (btnDownloadAmzip) {
    btnDownloadAmzip.addEventListener('click', async () => {
      showLoading(true, 'Creating .amzip Package...', 'Bundling project XML, photos & animation layers...');
      try {
        const { blob, filename } = await generateProjectPackage('amzip');
        triggerDownload(blob, filename);
        showLoading(false);
        showToast(filename + ' downloaded! Tap to import into After Motion Z.', 'success');
      } catch (err) {
        showLoading(false);
        showToast('Download error: ' + err.message, 'error');
      }
    });
  }

  // Manual Download XML Action (Pure XML)
  if (btnDownloadXml) {
    btnDownloadXml.addEventListener('click', async () => {
      showLoading(true, 'Generating Project XML...', 'Compiling typography and text layers...');
      try {
        const { blob, filename } = await generateProjectPackage('xml');
        triggerDownload(blob, filename);
        showLoading(false);
        showToast(filename + ' downloaded! Open it with After Motion Z.', 'success');
      } catch (err) {
        showLoading(false);
        showToast('Download error: ' + err.message, 'error');
      }
    });
  }

  btnStartNew.addEventListener('click', () => {
    if (confirm('Do you want to create a new invitation?')) {
      currentCardFiles = [];
      externalThumbnailUrl = '';
      groomPhotoFile = null;
      bridePhotoFile = null;
      updatePhotoUiState();
      renderCardThumbnails();
      if (typeof closeFloatingWidget === 'function') closeFloatingWidget();
      const elHeaderName = document.getElementById('headerProjectName');
      const elHeaderSub = document.getElementById('headerProjectSub');
      if (elHeaderName) elHeaderName.textContent = 'VivahEdit AI';
      if (elHeaderSub) elHeaderSub.textContent = 'After Motion Z Automation';
      showStep(1);
    }
  });

  // Modals Management
  if (btnOpenQr && modalQr) {
    btnOpenQr.addEventListener('click', () => modalQr.classList.remove('hidden'));
  }
  if (btnCloseQr && modalQr) {
    btnCloseQr.addEventListener('click', () => modalQr.classList.add('hidden'));
  }
  if (modalQr) {
    modalQr.addEventListener('click', (e) => {
      if (e.target === modalQr) modalQr.classList.add('hidden');
    });
  }

  // Admin Auth Modal for Settings (Password: 7067)
  const modalAdminAuth = document.getElementById('modalAdminAuth');
  const inpAdminPassword = document.getElementById('inpAdminPassword');
  const btnConfirmAuth = document.getElementById('btnConfirmAuth');
  const btnCancelAuth = document.getElementById('btnCancelAuth');
  const authErrorMsg = document.getElementById('authErrorMsg');

  // Global modal close helpers accessible anywhere & from inline onclick
  window.closeSettingsModal = function() {
    if (modalSettings) modalSettings.classList.add('hidden');
  };

  window.closeScannedFolderModal = function() {
    if (modalScannedCards) modalScannedCards.classList.add('hidden');
  };

  // Open Settings directly without secondary password prompt
  if (btnSettings) {
    btnSettings.addEventListener('click', () => {
      if (modalSettings) modalSettings.classList.remove('hidden');
      updateSettingsScannedCount();
      if (window.history && window.history.pushState) {
        window.history.pushState({ modal: 'settings' }, '');
      }
    });
  }

  const btnSettingsOpenFolder = document.getElementById('btnSettingsOpenFolder');
  if (btnSettingsOpenFolder) {
    btnSettingsOpenFolder.addEventListener('click', () => {
      window.closeSettingsModal();
      openScannedFolder();
    });
  }

  function updateSettingsScannedCount() {
    const sBadge = document.getElementById('settingsScannedCount');
    authFetch('/api/scanned-cards')
      .then(r => r.json())
      .then(res => {
        if (res.success && Array.isArray(res.cards)) {
          if (sBadge) sBadge.textContent = `${res.cards.length} Saved`;
          if (scannedCardsCountBadge) scannedCardsCountBadge.textContent = res.cards.length;
        }
      })
      .catch(() => {});
  }

  // ==================== DEDICATED SCANNED CARDS FOLDER MODAL ====================
  const modalScannedCards = document.getElementById('modalScannedCards');
  const btnOpenScannedFolder = document.getElementById('btnOpenScannedFolder');
  const btnCloseScannedFolder = document.getElementById('btnCloseScannedFolder');
  const btnRefreshScannedCards = document.getElementById('btnRefreshScannedCards');
  const inpSearchScannedCards = document.getElementById('inpSearchScannedCards');
  const scannedCardsCountBadge = document.getElementById('scannedCardsCountBadge');
  const scannedCardsListDetailed = document.getElementById('scannedCardsListDetailed');

  let cachedScannedCards = [];

  function openScannedFolder() {
    if (!modalScannedCards) return;
    modalScannedCards.classList.remove('hidden');
    loadScannedCardsDetailed();
    if (window.history && window.history.pushState) {
      window.history.pushState({ modal: 'scannedCards' }, '');
    }
  }

  if (btnOpenScannedFolder) btnOpenScannedFolder.addEventListener('click', openScannedFolder);
  if (btnCloseScannedFolder) btnCloseScannedFolder.addEventListener('click', window.closeScannedFolderModal);
  if (btnRefreshScannedCards) btnRefreshScannedCards.addEventListener('click', () => loadScannedCardsDetailed());
  if (modalScannedCards) {
    modalScannedCards.addEventListener('click', (e) => {
      if (e.target === modalScannedCards) window.closeScannedFolderModal();
    });
  }

  if (inpSearchScannedCards) {
    inpSearchScannedCards.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase().trim();
      if (!cachedScannedCards || cachedScannedCards.length === 0) return;
      const filtered = cachedScannedCards.filter(c => {
        const d = c.data || {};
        const text = `${c.groom_name} ${c.bride_name} ${c.pariwar_name} ${d.groom_village || ''} ${d.venue_gram || ''}`.toLowerCase();
        return text.includes(q);
      });
      renderDetailedCardsList(filtered);
    });
  }

  async function loadScannedCardsDetailed() {
    if (!scannedCardsListDetailed) return;
    scannedCardsListDetailed.innerHTML = '<div class="text-center py-8 text-xs text-white/40"><i class="fa-solid fa-spinner animate-spin text-amber-400 text-sm mb-1"></i><div>Loading scanned cards...</div></div>';

    try {
      const resp = await authFetch('/api/scanned-cards');
      const res = await resp.json();
      if (res.success && Array.isArray(res.cards)) {
        cachedScannedCards = res.cards;
        if (scannedCardsCountBadge) scannedCardsCountBadge.textContent = cachedScannedCards.length;
        const sBadge = document.getElementById('settingsScannedCount');
        if (sBadge) sBadge.textContent = `${cachedScannedCards.length} Saved`;
        renderDetailedCardsList(cachedScannedCards);
      } else {
        scannedCardsListDetailed.innerHTML = '<div class="text-center py-8 text-xs text-rose-400">Failed to load cards</div>';
      }
    } catch (err) {
      scannedCardsListDetailed.innerHTML = `<div class="text-center py-8 text-xs text-rose-400">Connection error: ${err.message}</div>`;
    }
  }

  function renderDetailedCardsList(cards) {
    if (!scannedCardsListDetailed) return;
    if (!cards || cards.length === 0) {
      scannedCardsListDetailed.innerHTML = `
        <div class="text-center py-8 px-4 bg-black/20 rounded-2xl border border-white/5 space-y-2">
          <div class="w-12 h-12 mx-auto rounded-full bg-amber-500/10 text-amber-300 flex items-center justify-center text-xl border border-amber-500/20">
            <i class="fa-solid fa-folder-open"></i>
          </div>
          <div class="text-xs font-semibold text-white/70">No saved cards found</div>
          <p class="text-[10px] text-white/40 max-w-xs mx-auto">Scanned cards and extracted details will be saved here automatically.</p>
        </div>
      `;
      return;
    }

    scannedCardsListDetailed.innerHTML = '';
    cards.forEach(card => {
      const d = card.data || {};
      const gName = d.groom_name || card.groom_name || 'Groom';
      const bName = d.bride_name || card.bride_name || 'Bride';
      const pariwar = d.pariwar_name || card.pariwar_name || '';
      const side = (d.card_side === 'bride') ? 'Bride Side' : 'Groom Side';
      const sideClass = (d.card_side === 'bride') ? 'text-pink-300 bg-pink-500/15 border-pink-500/30' : 'text-blue-300 bg-blue-500/15 border-blue-500/30';

      const eventsSummary = [d.event1_title, d.event2_title, d.event3_title, d.event4_title].filter(Boolean).join(' • ');
      const thumbSrc = card.has_thumbnail ? `/api/scanned-cards/${encodeURIComponent(card.scan_id)}/thumbnail` : '';

      const cardDiv = document.createElement('div');
      cardDiv.className = 'glass-card bg-neutral-950/70 border border-white/10 hover:border-amber-400/40 rounded-2xl p-3 space-y-2 transition shadow-lg';

      cardDiv.innerHTML = `
        <div class="flex items-start justify-between gap-2.5">
          <div class="flex items-center gap-2.5 min-w-0">
            ${thumbSrc 
              ? `<img src="${thumbSrc}" onerror="this.onerror=null; this.classList.add('hidden'); if(this.nextElementSibling) this.nextElementSibling.classList.remove('hidden');" class="w-12 h-12 object-cover rounded-xl border border-white/15 shrink-0 shadow" alt="Card" /><div class="hidden w-12 h-12 rounded-xl bg-amber-500/15 border border-amber-500/30 text-amber-300 flex items-center justify-center shrink-0 text-base"><i class="fa-solid fa-envelope-open-text"></i></div>` 
              : `<div class="w-12 h-12 rounded-xl bg-amber-500/15 border border-amber-500/30 text-amber-300 flex items-center justify-center shrink-0 text-base"><i class="fa-solid fa-envelope-open-text"></i></div>`
            }
            <div class="min-w-0">
              <div class="flex items-center gap-1.5 flex-wrap">
                <span class="text-[10px] px-2 py-0.5 rounded-full border font-bold ${sideClass}">${side}</span>
                <span class="text-[10px] text-white/40 font-mono">${card.date_formatted || ''}</span>
              </div>
              <h4 class="text-xs sm:text-sm font-bold text-white truncate mt-0.5">${gName} & ${bName}</h4>
              <p class="text-[10px] text-amber-200/80 truncate">${pariwar ? pariwar + ' • ' : ''}${d.groom_village || d.venue_gram || ''}</p>
            </div>
          </div>
          <button type="button" class="btn-del-record p-1.5 rounded-lg bg-rose-500/15 hover:bg-rose-500/25 text-rose-300 text-xs border border-rose-500/20 shrink-0 transition" title="Delete">
            <i class="fa-solid fa-trash text-xs"></i>
          </button>
        </div>

        ${eventsSummary ? `
          <div class="text-[10px] text-white/50 bg-black/40 px-2 py-1 rounded-lg border border-white/5 truncate">
            <i class="fa-solid fa-calendar-day text-amber-400/70 mr-1"></i>${eventsSummary}
          </div>
        ` : ''}

        <button type="button" class="btn-use-record w-full py-2 px-3 rounded-xl bg-gradient-to-r from-amber-500/25 via-emerald-600/25 to-teal-600/25 hover:from-amber-500/40 hover:to-emerald-600/40 text-amber-300 hover:text-white font-bold text-xs border border-amber-500/40 flex items-center justify-center gap-2 transition shadow">
          <i class="fa-solid fa-arrow-right-to-bracket text-xs"></i>
          <span>Use Details in Editor</span>
        </button>
      `;

      // Use Details button click
      cardDiv.querySelector('.btn-use-record').addEventListener('click', () => {
        populateForm(d);
        weddingData = d;
        if (thumbSrc) {
          externalThumbnailUrl = thumbSrc;
          updateFloatingCardView();
        }
        modalScannedCards.classList.add('hidden');
        if (modalSettings) modalSettings.classList.add('hidden');
        showStep(2);
        closeFloatingWidget();
        showToast(`Loaded: ${gName} & ${bName}! You can now edit or export.`, 'success');
      });

      // Delete button click
      cardDiv.querySelector('.btn-del-record').addEventListener('click', async () => {
        if (!confirm(`Delete record for ${gName} & ${bName}?`)) return;
        try {
          const dResp = await authFetch(`/api/scanned-cards/${encodeURIComponent(card.scan_id)}`, { method: 'DELETE' });
          const dJson = await dResp.json();
          if (dJson.success) {
            showToast('Record deleted', 'success');
            loadScannedCardsDetailed();
            updateSettingsScannedCount();
          }
        } catch (err) {
          showToast('Failed to delete', 'error');
        }
      });

      scannedCardsListDetailed.appendChild(cardDiv);
    });
  }

  // Load and manage Scanned Shadi Cards History
  function loadScannedCardsHistory() {
    loadScannedCardsDetailed();
  }

  if (btnConfirmAuth && typeof verifyAdminAuth === 'function') {
    btnConfirmAuth.addEventListener('click', verifyAdminAuth);
  }
  if (inpAdminPassword && typeof verifyAdminAuth === 'function') {
    inpAdminPassword.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') verifyAdminAuth();
    });
  }
  if (btnCancelAuth && modalAdminAuth) {
    btnCancelAuth.addEventListener('click', () => {
      modalAdminAuth.classList.add('hidden');
    });
  }
  if (modalAdminAuth) {
    modalAdminAuth.addEventListener('click', (e) => {
      if (e.target === modalAdminAuth) modalAdminAuth.classList.add('hidden');
    });
  }

  if (btnCloseSettings) btnCloseSettings.addEventListener('click', window.closeSettingsModal);
  const btnBottomCloseSettings = document.getElementById('btnBottomCloseSettings');
  if (btnBottomCloseSettings) btnBottomCloseSettings.addEventListener('click', window.closeSettingsModal);

  if (modalSettings) {
    modalSettings.addEventListener('click', (e) => {
      if (e.target === modalSettings) window.closeSettingsModal();
    });
  }

  // Global Escape key listener to close modals
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      window.closeSettingsModal();
      window.closeScannedFolderModal();
      window.closeAfterMotionGuideModal();
      closeCardViewer();
      if (modalAdminAuth) modalAdminAuth.classList.add('hidden');
    }
  });

  // Mobile Android Hardware Back Button & Browser History Controller
  window.addEventListener('popstate', (e) => {
    // 0. Close After Motion Guide modal if open
    if (modalAfterMotionGuide && !modalAfterMotionGuide.classList.contains('hidden')) {
      window.closeAfterMotionGuideModal();
      return;
    }
    // 1. Close full screen viewer if open
    if (modalCardViewer && !modalCardViewer.classList.contains('hidden')) {
      closeCardViewer();
      return;
    }
    // 2. Close Scanned Cards Folder modal if open
    if (modalScannedCards && !modalScannedCards.classList.contains('hidden')) {
      window.closeScannedFolderModal();
      return;
    }
    // 3. Close Settings modal if open
    if (modalSettings && !modalSettings.classList.contains('hidden')) {
      window.closeSettingsModal();
      return;
    }
    // 4. Close QR modal if open
    if (modalQr && !modalQr.classList.contains('hidden')) {
      modalQr.classList.add('hidden');
      return;
    }
    // 5. Close Admin Auth modal if open
    if (modalAdminAuth && !modalAdminAuth.classList.contains('hidden')) {
      modalAdminAuth.classList.add('hidden');
      return;
    }
    // 6. Close card sidebar drawer if open
    if (isSidebarOpen) {
      closeCardSidebar();
      return;
    }
    // 7. Step back navigation
    if (e.state && typeof e.state.step === 'number') {
      showStep(e.state.step, false);
    } else {
      if (currentActiveStep === 3) {
        showStep(2, false);
      } else if (currentActiveStep === 2) {
        showStep(1, false);
      }
    }
  });



  // Change Editor Passcode (Admin Protected)
  const inpNewEditorPass = document.getElementById('inpNewEditorPass');
  const btnToggleNewPassEye = document.getElementById('btnToggleNewPassEye');
  const newPassEyeIcon = document.getElementById('newPassEyeIcon');
  const btnSaveNewEditorPass = document.getElementById('btnSaveNewEditorPass');

  if (btnToggleNewPassEye && inpNewEditorPass) {
    btnToggleNewPassEye.addEventListener('click', () => {
      if (inpNewEditorPass.type === 'password') {
        inpNewEditorPass.type = 'text';
        if (newPassEyeIcon) newPassEyeIcon.className = 'fa-solid fa-eye-slash';
      } else {
        inpNewEditorPass.type = 'password';
        if (newPassEyeIcon) newPassEyeIcon.className = 'fa-solid fa-eye';
      }
    });
  }

  if (btnSaveNewEditorPass) {
    btnSaveNewEditorPass.addEventListener('click', async () => {
      const newPass = (inpNewEditorPass?.value || '').trim();
      if (!newPass || newPass.length < 4) {
        showToast('Passcode must be at least 4 characters!', 'error');
        return;
      }

      showLoading(true, 'Updating Passcode...', 'Updating security credentials and rotating tokens...');
      try {
        const resp = await fetch('/api/auth/change-password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            admin_password: '7067',
            new_editor_password: newPass
          })
        });
        const resData = await resp.json();
        showLoading(false);
        if (resp.ok && resData.success) {
          if (resData.new_token) {
            setAuthToken(resData.new_token, true);
          }
          if (inpNewEditorPass) inpNewEditorPass.value = '';
          modalSettings.classList.add('hidden');
          showToast('Editor passcode updated! All previous sessions revoked.', 'success');
        } else {
          showToast(resData.error || 'Failed to update passcode', 'error');
        }
      } catch (err) {
        showLoading(false);
        showToast('Error: ' + err.message, 'error');
      }
    });
  }

  // UI Utilities
  function showLoading(show, title = '', sub = '') {
    if (show) {
      loadingTitle.textContent = title;
      loadingSub.textContent = sub;
      loadingOverlay.classList.remove('hidden');
    } else {
      loadingOverlay.classList.add('hidden');
    }
  }

  function showToast(msg, type = 'info', duration = 3500) {
    const toast = document.getElementById('toast');
    if (!toast) return;

    let iconClass = 'fa-solid fa-circle-info text-amber-400';
    let borderClass = 'border-amber-500/40 text-amber-200';

    if (type === 'success') {
      iconClass = 'fa-solid fa-circle-check text-emerald-400';
      borderClass = 'border-emerald-500/40 text-emerald-200';
    } else if (type === 'error') {
      iconClass = 'fa-solid fa-circle-exclamation text-rose-400';
      borderClass = 'border-rose-500/40 text-rose-200';
    }

    toast.className = `fixed bottom-5 left-1/2 -translate-x-1/2 z-50 px-4 py-2.5 rounded-2xl text-xs font-semibold shadow-2xl transition duration-300 flex items-center gap-2 border bg-neutral-950/95 backdrop-blur-md ${borderClass}`;
    toast.innerHTML = `<i class="${iconClass}"></i><span>${msg}</span>`;
    toast.classList.remove('hidden');

    if (window._toastTimer) clearTimeout(window._toastTimer);
    window._toastTimer = setTimeout(() => {
      toast.classList.add('hidden');
    }, duration);
  }

  // Ensure Smart Mobile Edge Tab and Header button are initialized on page load
  try {
    if (typeof updateSidebarEdgeTabVisibility === 'function') updateSidebarEdgeTabVisibility();
    if (typeof updateHeaderWatchCardButton === 'function') updateHeaderWatchCardButton();
  } catch (_) {}
});
