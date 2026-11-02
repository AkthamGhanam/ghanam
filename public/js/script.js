        function toggleSearch() {
            const overlay = document.getElementById('search-overlay');
            const isOpening = !overlay.classList.contains('active');
            
            if (isOpening) {
                overlay.style.display = 'flex';
                // Pequeño delay para que la transición de opacidad funcione
                setTimeout(() => {
                    overlay.classList.add('active');
                    document.getElementById('mobile-search-input').focus();
                }, 10);
            } else {
                overlay.classList.remove('active');
                setTimeout(() => {
                    overlay.style.display = 'none';
                }, 400);
            }
        }

        // Cerrar con tecla Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && document.getElementById('search-overlay').classList.contains('active')) {
                toggleSearch();
            }
        });