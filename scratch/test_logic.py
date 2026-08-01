class Test:
    @classmethod
    def _obter_id_nota_origem_valido(cls, id_nota_origem, id_nota_atual, id_produto, id_tipo_nota):
        if id_tipo_nota == 1:
            return id_nota_atual
        if id_nota_origem is not None:
            try:
                id_orig_int = int(id_nota_origem)
                if id_orig_int != int(id_nota_atual):
                    # WAIT, what if it explicitly rejects 0?
                    if id_orig_int > 0:
                        return id_orig_int
            except (ValueError, TypeError):
                pass
        return 999

print(Test._obter_id_nota_origem_valido(0, 53, 2, 4))
