// Sistema de notificações AMEG
class NotificationSystem {
    constructor() {
        this.container = null;
        this.init();
    }
    
    init() {
        this.createContainer();
        this.loadNotifications();
        setInterval(() => this.loadNotifications(), 30000); // Atualiza a cada 30s
    }
    
    createContainer() {
        this.container = document.createElement('div');
        this.container.id = 'notifications-container';
        this.container.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 1000;
            max-width: 350px; pointer-events: none;
        `;
        document.body.appendChild(this.container);
    }
    
    async loadNotifications() {
        try {
            const response = await fetch('/api/notifications');
            const notifications = await response.json();
            this.displayNotifications(notifications);
        } catch (error) {
            console.error('Erro ao carregar notificações:', error);
        }
    }
    
    displayNotifications(notifications) {
        // Limpa notificações antigas
        this.container.innerHTML = '';
        
        notifications.forEach((notif, index) => {
            setTimeout(() => this.showNotification(notif), index * 200);
        });
    }
    
    showNotification(notif) {
        const div = document.createElement('div');
        div.className = `notification ${notif.priority}`;
        div.style.cssText = `
            background: ${this.getColor(notif.priority)};
            color: white; padding: 12px; margin-bottom: 10px;
            border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            pointer-events: auto; cursor: pointer;
            transform: translateX(100%); transition: transform 0.3s ease;
        `;
        
        div.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 18px;">${notif.icon}</span>
                <span style="font-size: 13px; line-height: 1.3;">${notif.message}</span>
            </div>
        `;
        
        div.onclick = () => this.removeNotification(div);
        this.container.appendChild(div);
        
        // Animação de entrada
        setTimeout(() => div.style.transform = 'translateX(0)', 100);
        
        // Remove automaticamente após 8 segundos
        setTimeout(() => this.removeNotification(div), 8000);
    }
    
    removeNotification(element) {
        element.style.transform = 'translateX(100%)';
        setTimeout(() => element.remove(), 300);
    }
    
    getColor(priority) {
        const colors = {
            urgent: '#dc3545',
            high: '#fd7e14', 
            medium: '#ffc107',
            low: '#28a745'
        };
        return colors[priority] || '#6c757d';
    }
}

// Inicializa quando a página carrega
document.addEventListener('DOMContentLoaded', () => {
    new NotificationSystem();
});
