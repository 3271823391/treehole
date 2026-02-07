// 统一测量 footer 高度，确保滚动容器预留安全空间。
function measureFooter() {
    const footer = document.getElementById('copyrightBar');
    if (!footer) return;
    const height = Math.ceil(footer.getBoundingClientRect().height || 0);
    document.documentElement.style.setProperty('--footer-h', `${height}px`);
}

function createInteractionStateManager() {
    const activeLayers = new Set();
    const lockClasses = ['ui-locked', 'modal-open', 'drawer-open', 'panel-open'];

    function syncLayerFlags() {
        const hasActiveLayer = activeLayers.size > 0;
        const value = hasActiveLayer ? 'true' : 'false';
        document.documentElement.dataset.uiLayerOpen = value;
        document.body?.dataset && (document.body.dataset.uiLayerOpen = value);
    }

    function clearGlobalInteractionLocks() {
        const targets = [document.documentElement, document.body].filter(Boolean);
        targets.forEach((node) => {
            node.style.pointerEvents = '';
            node.style.overflow = '';
            node.style.overflowX = '';
            node.style.overflowY = '';
            node.style.touchAction = '';
            node.style.userSelect = '';
            lockClasses.forEach((name) => node.classList.remove(name));
        });
    }

    return {
        setLayerOpen(layer, open) {
            if (!layer) return;
            if (open) {
                activeLayers.add(layer);
            } else {
                activeLayers.delete(layer);
            }
            syncLayerFlags();
            if (!open) {
                clearGlobalInteractionLocks();
            }
        },
        reset() {
            activeLayers.clear();
            syncLayerFlags();
            clearGlobalInteractionLocks();
        }
    };
}

window.SharedShellInteraction = createInteractionStateManager();

function recoverSharedInteractionState() {
    if (window.SharedShellInteraction?.reset) {
        window.SharedShellInteraction.reset();
    }
    const targets = [document.documentElement, document.body, document.getElementById('appShell')].filter(Boolean);
    targets.forEach((node) => {
        node.removeAttribute('inert');
        node.style.pointerEvents = '';
        node.style.overflow = '';
        node.style.overflowX = '';
        node.style.overflowY = '';
        node.style.touchAction = '';
        node.style.userSelect = '';
    });
    ['ui-locked', 'modal-open', 'drawer-open', 'panel-open'].forEach((lockClass) => {
        document.documentElement.classList.remove(lockClass);
        document.body?.classList.remove(lockClass);
    });

    document.querySelectorAll('.modal-backdrop.active, .drawer-backdrop.active, .overlay.active, .mask.active').forEach((layer) => {
        layer.classList.remove('active');
        if (layer.hasAttribute('aria-hidden')) {
            layer.setAttribute('aria-hidden', 'true');
        }
    });

    document.querySelectorAll('.mobile-panel[data-visible="true"]').forEach((panel) => {
        panel.dataset.visible = 'false';
    });
}

document.addEventListener('DOMContentLoaded', recoverSharedInteractionState);
window.addEventListener('load', measureFooter);
window.addEventListener('resize', measureFooter);
window.addEventListener('pageshow', recoverSharedInteractionState);
window.addEventListener('focus', recoverSharedInteractionState);
window.addEventListener('popstate', recoverSharedInteractionState);
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
        recoverSharedInteractionState();
    }
});
