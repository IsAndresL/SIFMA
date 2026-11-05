// SIFMA — Enrutador Dinámico Modular de Vistas
// Carga bajo demanda HTML, CSS y JS específicos de cada funcionalidad sin recarga de ventana.

const MODULE_HEADERS = {
    dashboard: {
        title: "Dashboard Analítico",
        subtitle: "Resumen general de la jornada y fenotipado"
    },
    vision_processing: {
        title: "Procesamiento de Visión Computacional",
        subtitle: "Segmentación ExG, umbralización de Otsu y extracción morfométrica"
    },
    gallery: {
        title: "Galería Fenotípica de Lotes",
        subtitle: "Inspección visual comparativa de capturas cenitales y laterales"
    },
    timelapse: {
        title: "Time-Lapse Evolutivo",
        subtitle: "Reproducción cinemática temporal del desarrollo foliar y caulinar"
    },
    telemetry_sensors: {
        title: "Telemetría de Sensores Ambientales",
        subtitle: "Monitoreo fisicoquímico en tiempo real de la solución hidropónica"
    },
    cross_analysis: {
        title: "Análisis Cruzado y Correlación de Pearson",
        subtitle: "Modelado estadístico multivariable entre clima y desarrollo biométrico"
    },
    scientific_dossier: {
        title: "Dossier Científico y Reportes",
        subtitle: "Expediente técnico formal para depósito DNDA y validación agronómica"
    },
    crop_config: {
        title: "Parámetros Botánicos de Cultivo",
        subtitle: "Configuración de umbrales óptimos por canastilla y especie"
    },
    user_management: {
        title: "Gestión de Usuarios y Roles",
        subtitle: "Control de acceso basado en roles (RBAC) y credenciales operativas"
    },
    audit_logs: {
        title: "Registro de Auditoría y Seguridad",
        subtitle: "Trazabilidad inmutable de eventos con verificación criptográfica SHA-256"
    },
    system_info: {
        title: "Información del Sistema y Créditos",
        subtitle: "Arquitectura híbrida Rust + Python Sidecar y autoría institucional"
    }
};

export class NavigationRouter {
    constructor(viewportElementId) {
        this.viewport = document.getElementById(viewportElementId);
        this.currentModule = null;
        this.activeStyleElement = null;
    }

    async loadModule(moduleName) {
        if (this.currentModule === moduleName) return;

        try {
            // 1. Actualizar encabezados superiores de la ventana
            this.updatePageHeader(moduleName);

            // 2. Cargar el HTML del módulo (relativo a index.html)
            const htmlPath = `/modules/${moduleName}/${moduleName}.html`;
            const htmlRes = await fetch(htmlPath);
            if (!htmlRes.ok) throw new Error(`No se pudo cargar ${htmlPath} (HTTP ${htmlRes.status})`);
            const htmlContent = await htmlRes.text();

            // 3. Intercambiar estilos CSS específicos
            this.swapModuleStyles(moduleName);

            // 4. Renderizar el HTML en el contenedor principal
            this.viewport.innerHTML = htmlContent;

            // 5. Importar dinámicamente el controlador JS del módulo
            // Nota: import() resuelve relativo a /core/scripts/navigation.js -> ../../modules/...
            const jsPath = `../../modules/${moduleName}/${moduleName}.js`;
            const moduleController = await import(jsPath);
            if (moduleController && typeof moduleController.initModule === 'function') {
                await moduleController.initModule();
            }

            this.currentModule = moduleName;
            this.updateActiveNavButton(moduleName);
        } catch (err) {
            console.error(`[ROUTER ERROR] Fallo al cargar el módulo '${moduleName}':`, err);
            this.viewport.innerHTML = `
                <div style="padding: 30px; text-align: center; color: #ef4444; background: rgba(255,255,255,0.92); border-radius: 12px; max-width: 600px; margin: 40px auto; box-shadow: 0 10px 25px rgba(0,0,0,0.15);">
                    <h2 style="margin-bottom: 8px;">Error de Carga Modular</h2>
                    <p>No fue posible cargar el módulo <code>${moduleName}</code>.</p>
                    <pre style="margin-top: 12px; font-size: 11px; background: #fee2e2; padding: 10px; border-radius: 6px; overflow-x: auto;">${err.message}</pre>
                </div>
            `;
        }
    }

    updatePageHeader(moduleName) {
        const headerMeta = MODULE_HEADERS[moduleName];
        if (!headerMeta) return;
        const headingEl = document.getElementById('page-heading');
        const subheadingEl = document.getElementById('page-subheading');
        if (headingEl) headingEl.textContent = headerMeta.title;
        if (subheadingEl) subheadingEl.textContent = headerMeta.subtitle;
    }

    swapModuleStyles(moduleName) {
        if (this.activeStyleElement) {
            this.activeStyleElement.remove();
            this.activeStyleElement = null;
        }

        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = `/modules/${moduleName}/${moduleName}.css`;
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
