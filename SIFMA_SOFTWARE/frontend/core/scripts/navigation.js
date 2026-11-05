// SIFMA — Enrutador Dinámico Modular de Vistas
// Carga bajo demanda HTML, CSS y JS específicos de cada funcionalidad sin recarga de ventana.

export class NavigationRouter {
    constructor(viewportElementId) {
        this.viewport = document.getElementById(viewportElementId);
        this.currentModule = null;
        this.activeStyleElement = null;
    }

    async loadModule(moduleName) {
        if (this.currentModule === moduleName) return;

        try {
            // 1. Cargar el HTML del módulo
            const htmlPath = `modules/${moduleName}/${moduleName}.html`;
            const htmlRes = await fetch(htmlPath);
            if (!htmlRes.ok) throw new Error(`No se pudo cargar ${htmlPath}`);
            const htmlContent = await htmlRes.text();

            // 2. Intercambiar estilos CSS específicos
            this.swapModuleStyles(moduleName);

            // 3. Renderizar el HTML en el contenedor principal
            this.viewport.innerHTML = htmlContent;

            // 4. Importar dinámicamente el controlador JS del módulo
            const jsPath = `../modules/${moduleName}/${moduleName}.js`;
            const moduleController = await import(jsPath);
            if (moduleController && typeof moduleController.initModule === 'function') {
                await moduleController.initModule();
            }

            this.currentModule = moduleName;
            this.updateActiveNavButton(moduleName);
        } catch (err) {
            console.error(`[ROUTER ERROR] Fallo al cargar el módulo '${moduleName}':`, err);
            this.viewport.innerHTML = `
                <div style="padding: 30px; text-align: center; color: var(--accent-rose);">
                    <h2>Error de Carga Modular</h2>
                    <p style="margin-top: 8px;">No fue posible cargar el módulo <code>${moduleName}</code>.</p>
                    <pre style="margin-top: 12px; font-size: 11px;">${err.message}</pre>
                </div>
            `;
        }
    }

    swapModuleStyles(moduleName) {
        if (this.activeStyleElement) {
            this.activeStyleElement.remove();
            this.activeStyleElement = null;
        }

        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = `modules/${moduleName}/${moduleName}.css`;
        document.head.appendChild(link);
        this.activeStyleElement = link;
    }

    updateActiveNavButton(moduleName) {
        document.querySelectorAll('.nav-link').forEach(link => {
            if (link.dataset.module === moduleName) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }
}

