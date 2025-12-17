document.addEventListener('DOMContentLoaded', function() {
    initTooltips();

    initModals();

    initFormValidations();

    initAnimations();

    setupLocalDatetime();
});

function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');

    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(e) {
    const tooltipText = this.getAttribute('data-tooltip');
    if (!tooltipText) return;

    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip';
    tooltip.textContent = tooltipText;
    tooltip.style.position = 'absolute';
    tooltip.style.zIndex = '9999';

    document.body.appendChild(tooltip);

    const rect = this.getBoundingClientRect();
    tooltip.style.top = (rect.top - tooltip.offsetHeight - 10) + 'px';
    tooltip.style.left = (rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2)) + 'px';

    this._tooltip = tooltip;
}

function hideTooltip() {
    if (this._tooltip) {
        this._tooltip.remove();
        this._tooltip = null;
    }
}

function initModals() {
    document.querySelectorAll('[data-modal-target]').forEach(button => {
        button.addEventListener('click', () => {
            const modalId = button.getAttribute('data-modal-target');
            const modal = document.getElementById(modalId);
            if (modal) {
                openModal(modal);
            }
        });
    });

    document.querySelectorAll('[data-modal-close]').forEach(button => {
        button.addEventListener('click', () => {
            const modal = button.closest('.modal');
            if (modal) {
                closeModal(modal);
            }
        });
    });

    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(modal);
            }
        });
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.show').forEach(modal => {
                closeModal(modal);
            });
        }
    });
}

function openModal(modal) {
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';

    const input = modal.querySelector('input, textarea, select');
    if (input) {
        setTimeout(() => input.focus(), 100);
    }
}

function closeModal(modal) {
    modal.classList.remove('show');
    document.body.style.overflow = '';
}

function initFormValidations() {
    document.querySelectorAll('input[type="email"]').forEach(input => {
        input.addEventListener('blur', validateEmail);
    });

    document.querySelectorAll('input[type="password"]').forEach(input => {
        input.addEventListener('input', validatePasswordStrength);
    });

    document.querySelectorAll('input[type="number"][min="0"]').forEach(input => {
        input.addEventListener('blur', validatePositiveNumber);
    });

    document.querySelectorAll('input[type="datetime-local"]').forEach(input => {
        input.addEventListener('change', validateFutureDate);
    });
}

function validateEmail(e) {
    const input = e.target;
    const email = input.value.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (email && !emailRegex.test(email)) {
        showInputError(input, 'Por favor, insira um email válido');
        return false;
    } else {
        clearInputError(input);
        return true;
    }
}

function validatePasswordStrength(e) {
    const input = e.target;
    const password = input.value;

    if (!password) {
        clearInputError(input);
        return;
    }

    let strength = 0;
    const feedback = [];

    if (password.length >= 8) {
        strength++;
    } else {
        feedback.push('Mínimo 8 caracteres');
    }

    if (/[A-Z]/.test(password)) {
        strength++;
    } else {
        feedback.push('Pelo menos uma letra maiúscula');
    }

    if (/[0-9]/.test(password)) {
        strength++;
    } else {
        feedback.push('Pelo menos um número');
    }

    if (/[^A-Za-z0-9]/.test(password)) {
        strength++;
    } else {
        feedback.push('Pelo menos um caractere especial');
    }

    const strengthMeter = input.parentElement.querySelector('.password-strength');
    if (strengthMeter) {
        const bars = strengthMeter.querySelectorAll('.strength-bar');
        bars.forEach((bar, index) => {
            bar.className = 'strength-bar';
            if (index < strength) {
                bar.classList.add('active');
                bar.classList.add(`strength-${strength}`);
            }
        });
    }

    if (strength < 3 && password.length > 0) {
        showInputError(input, feedback.join(', '));
    } else {
        clearInputError(input);
    }
}

function validatePositiveNumber(e) {
    const input = e.target;
    const value = parseFloat(input.value);

    if (isNaN(value) || value < 0) {
        showInputError(input, 'Por favor, insira um número positivo');
        return false;
    } else {
        clearInputError(input);
        return true;
    }
}

function validateFutureDate(e) {
    const input = e.target;
    const selectedDate = new Date(input.value);
    const now = new Date();

    if (selectedDate < now) {
        showInputError(input, 'Por favor, selecione uma data futura');
        return false;
    } else {
        clearInputError(input);
        return true;
    }
}

function showInputError(input, message) {
    clearInputError(input);

    const errorDiv = document.createElement('div');
    errorDiv.className = 'input-error';
    errorDiv.textContent = message;
    errorDiv.style.color = '#E74C3C';
    errorDiv.style.fontSize = '0.85rem';
    errorDiv.style.marginTop = '5px';

    input.parentElement.appendChild(errorDiv);
    input.style.borderColor = '#E74C3C';

    input._errorDiv = errorDiv;
}

function clearInputError(input) {
    if (input._errorDiv) {
        input._errorDiv.remove();
        input._errorDiv = null;
    }
    input.style.borderColor = '';
}

function initAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        observer.observe(el);
    });

    setTimeout(() => {
        document.body.classList.add('loaded');
    }, 100);
}

function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatRelativeTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'agora mesmo';
    if (diffMins < 60) return `há ${diffMins} minuto${diffMins > 1 ? 's' : ''}`;
    if (diffHours < 24) return `há ${diffHours} hora${diffHours > 1 ? 's' : ''}`;
    if (diffDays < 7) return `há ${diffDays} dia${diffDays > 1 ? 's' : ''}`;

    return formatDate(dateString);
}

async function apiRequest(endpoint, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    };

    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };

    try {
        const response = await fetch(endpoint, mergedOptions);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }

        return await response.text();
    } catch (error) {
        console.error('API Request Error:', error);
        showNotification('Erro na requisição. Tente novamente.', 'error');
        throw error;
    }
}

function showNotification(message, type = 'info', duration = 5000) {
    const existing = document.querySelector('.notification-container');
    if (existing) existing.remove();

    // Criar container
    const container = document.createElement('div');
    container.className = 'notification-container';
    container.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 99999;
    `;

    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        background: ${type === 'success' ? '#2ECC71' :
                     type === 'error' ? '#E74C3C' :
                     type === 'warning' ? '#F39C12' : '#3498DB'};
        color: white;
        padding: 15px 20px;
        border-radius: 10px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        animation: slideInRight 0.3s ease;
    `;

    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' :
                          type === 'error' ? 'exclamation-circle' :
                          type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
        <span>${message}</span>
        <button class="notification-close" style="
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            margin-left: auto;
            padding: 0 5px;
        ">
            <i class="fas fa-times"></i>
        </button>
    `;

    notification.querySelector('.notification-close').addEventListener('click', () => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    });

    container.appendChild(notification);
    document.body.appendChild(container);

    if (duration > 0) {
        setTimeout(() => {
            if (notification.parentElement) {
                notification.style.animation = 'slideOutRight 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }
        }, duration);
    }

    if (!document.querySelector('#notification-animations')) {
        const style = document.createElement('style');
        style.id = 'notification-animations';
        style.textContent = `
            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }

            @keyframes slideOutRight {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

async function copyToClipboard(text, showNotification = true) {
    try {
        await navigator.clipboard.writeText(text);
        if (showNotification) {
            showNotification('Copiado para a área de transferência!', 'success', 2000);
        }
        return true;
    } catch (err) {
        console.error('Erro ao copiar:', err);

        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.select();

        try {
            document.execCommand('copy');
            if (showNotification) {
                showNotification('Copiado para a área de transferência!', 'success', 2000);
            }
            return true;
        } catch (err2) {
            console.error('Fallback copy failed:', err2);
            if (showNotification) {
                showNotification('Erro ao copiar. Tente manualmente.', 'error', 3000);
            }
            return false;
        } finally {
            document.body.removeChild(textArea);
        }
    }
}

function confirmAction(message, callback) {
    let modal = document.getElementById('confirmationModal');

    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'confirmationModal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 500px;">
                <div class="modal-header">
                    <h3><i class="fas fa-exclamation-triangle"></i> Confirmação</h3>
                    <button class="btn-close" data-modal-close>&times;</button>
                </div>
                <div class="modal-body">
                    <p id="confirmationMessage"></p>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" id="confirmCancel">Cancelar</button>
                    <button class="btn btn-danger" id="confirmOk">Confirmar</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        if (!document.querySelector('#modal-styles')) {
            const style = document.createElement('style');
            style.id = 'modal-styles';
            style.textContent = `
                .modal {
                    display: none;
                    position: fixed;
                    z-index: 9999;
                    left: 0;
                    top: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(0,0,0,0.5);
                }

                .modal.show {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                .modal-content {
                    background: white;
                    border-radius: 10px;
                    padding: 0;
                    animation: modalFadeIn 0.3s;
                }

                @keyframes modalFadeIn {
                    from { opacity: 0; transform: translateY(-20px); }
                    to { opacity: 1; transform: translateY(0); }
                }
            `;
            document.head.appendChild(style);
        }
    }

    document.getElementById('confirmationMessage').textContent = message;

    const cancelBtn = document.getElementById('confirmCancel');
    const okBtn = document.getElementById('confirmOk');

    const newCancelBtn = cancelBtn.cloneNode(true);
    const newOkBtn = okBtn.cloneNode(true);

    cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);
    okBtn.parentNode.replaceChild(newOkBtn, okBtn);

    newCancelBtn.addEventListener('click', () => closeModal(modal));
    newOkBtn.addEventListener('click', () => {
        closeModal(modal);
        if (typeof callback === 'function') {
            callback();
        }
    });

    modal.querySelector('[data-modal-close]').addEventListener('click', () => closeModal(modal));

    openModal(modal);
}


function setupLocalDatetime() {
    const datetimeInputs = document.querySelectorAll('input[type="datetime-local"]');
    datetimeInputs.forEach(input => {
        if (!input.value) {
            const now = new Date();
            now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
            input.min = now.toISOString().slice(0, 16);
        }
    });
}

window.AppUtils = {
    showNotification,
    confirmAction,
    copyToClipboard,
    formatCurrency,
    formatDate,
    formatRelativeTime,
    apiRequest
};

const dynamicStyles = `
    .custom-tooltip {
        background: #333;
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 0.85rem;
        max-width: 200px;
        text-align: center;
        box-shadow: 0 3px 10px rgba(0,0,0,0.2);
        pointer-events: none;
    }

    .custom-tooltip::after {
        content: '';
        position: absolute;
        top: 100%;
        left: 50%;
        margin-left: -5px;
        border-width: 5px;
        border-style: solid;
        border-color: #333 transparent transparent transparent;
    }

    .password-strength {
        display: flex;
        gap: 5px;
        margin-top: 10px;
    }

    .strength-bar {
        flex: 1;
        height: 5px;
        background: #ddd;
        border-radius: 3px;
        transition: all 0.3s;
    }

    .strength-bar.active {
        background: #FF6B6B;
    }

    .strength-bar.active.strength-1 { background: #FF6B6B; }
    .strength-bar.active.strength-2 { background: #F39C12; }
    .strength-bar.active.strength-3 { background: #3498DB; }
    .strength-bar.active.strength-4 { background: #2ECC71; }

    .animate-on-scroll {
        opacity: 0;
        transform: translateY(20px);
        transition: opacity 0.6s, transform 0.6s;
    }

    .animate-on-scroll.animated {
        opacity: 1;
        transform: translateY(0);
    }

    .loaded .page-transition {
        animation: fadeIn 0.5s ease;
    }

    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
`;

const styleElement = document.createElement('style');
styleElement.textContent = dynamicStyles;

document.head.appendChild(styleElement);
