/* Sazonalizei — utilitários globais compartilhados por todas as páginas */

// ── Menu lateral (mobile) ──────────────────────────────────────────────
function abrirSidebar() {
    document.getElementById('sidebar')?.classList.add('open');
    document.getElementById('sidebar-overlay')?.classList.add('active');
}

function fecharSidebar() {
    document.getElementById('sidebar')?.classList.remove('open');
    document.getElementById('sidebar-overlay')?.classList.remove('active');
}

// ── Relógio da barra superior ──────────────────────────────────────────
function atualizarRelogioTopbar() {
    const el = document.getElementById('topbar-datetime');
    if (!el) return;
    const agora = new Date();
    const data = agora.toLocaleDateString('pt-BR');
    const hora = agora.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    el.textContent = `📅 ${data} · ${hora}`;
}

document.addEventListener('DOMContentLoaded', () => {
    atualizarRelogioTopbar();
    setInterval(atualizarRelogioTopbar, 30000);

    // Fecha qualquer modal com a classe .modal-overlay ao clicar fora da caixa
    document.querySelectorAll('.modal-overlay').forEach((overlay) => {
        overlay.addEventListener('click', (evento) => {
            if (evento.target === overlay) {
                overlay.classList.remove('active');
            }
        });
    });

    // Fecha o menu mobile automaticamente ao navegar
    document.querySelectorAll('.nav-link').forEach((link) => {
        link.addEventListener('click', fecharSidebar);
    });
});

// Atalhos de teclado citados na sidebar (F1 = PDV, F4 = Financeiro)
document.addEventListener('keydown', (evento) => {
    if (evento.key === 'F1') {
        const link = document.querySelector('a[href*="pdv"]');
        if (link) { evento.preventDefault(); window.location.href = link.href; }
    }
    if (evento.key === 'F4') {
        const link = document.querySelector('a[href*="financeiro"]');
        if (link) { evento.preventDefault(); window.location.href = link.href; }
    }
});
