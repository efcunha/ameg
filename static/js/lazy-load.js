// Sistema de Lazy Loading Otimizado para AMEG
class LazyLoader {
    constructor() {
        this.imageObserver = null;
        this.init();
    }

    init() {
        // Verifica suporte ao Intersection Observer
        if ('IntersectionObserver' in window) {
            this.imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.loadImage(entry.target);
                        this.imageObserver.unobserve(entry.target);
                    }
                });
            }, {
                rootMargin: '50px 0px', // Carrega 50px antes de aparecer
                threshold: 0.01
            });
            
            this.observeImages();
        } else {
            // Fallback para navegadores antigos
            this.loadAllImages();
        }
    }

    observeImages() {
        const lazyImages = document.querySelectorAll('img[data-src]');
        lazyImages.forEach(img => {
            this.imageObserver.observe(img);
            // Adiciona placeholder enquanto carrega
            if (!img.src) {
                img.src = this.createPlaceholder(img.dataset.width || 300, img.dataset.height || 200);
            }
        });
    }

    loadImage(img) {
        const src = img.dataset.src;
        if (!src) return;

        // Pré-carrega a imagem
        const imageLoader = new Image();
        imageLoader.onload = () => {
            img.src = src;
            img.classList.add('loaded');
            img.removeAttribute('data-src');
        };
        imageLoader.onerror = () => {
            img.classList.add('error');
            img.alt = 'Erro ao carregar imagem';
        };
        imageLoader.src = src;
    }

    createPlaceholder(width, height) {
        // Cria placeholder SVG leve
        const svg = `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#f0f0f0"/>
            <text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="#999">Carregando...</text>
        </svg>`;
        return 'data:image/svg+xml;base64,' + btoa(svg);
    }

    loadAllImages() {
        // Fallback: carrega todas as imagens imediatamente
        const lazyImages = document.querySelectorAll('img[data-src]');
        lazyImages.forEach(img => this.loadImage(img));
    }
}

// CSS para transições suaves
const style = document.createElement('style');
style.textContent = `
    img[data-src] {
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    img.loaded {
        opacity: 1;
    }
    img.error {
        opacity: 0.5;
        filter: grayscale(100%);
    }
`;
document.head.appendChild(style);

// Inicializa quando DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new LazyLoader());
} else {
    new LazyLoader();
}
