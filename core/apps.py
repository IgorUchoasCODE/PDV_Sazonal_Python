from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        """
        Tenta carregar o backend real (InventoryManager) do banco SQLite
        próprio (databaseSazonalizei.db) assim que o servidor Django sobe.

        Isso é 'melhor esforço': se o backend ou o banco não estiverem
        disponíveis/compatíveis por algum motivo, o site continua no ar
        normalmente e cada view usa dados de demonstração como reserva
        (veja core/helpers.py).
        """
        try:
            from br.com.pdv.src.memory.inventoryManager import InventoryManager
            InventoryManager.carregarTudo()
        except Exception as exc:  # pragma: no cover
            print(f"[core.apps] Aviso: não foi possível carregar o InventoryManager na subida: {exc}")
