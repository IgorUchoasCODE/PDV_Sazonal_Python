from br.com.pdv.src.financeiro import Real
from br.com.pdv.src.financeiro import Real
from br.com.pdv.src.produto.UnidadeMedida import UnidadeMedida, UnidadeConjunto
from br.com.pdv.src.financeiro.Real import MoedaReal
from typing import Union



class Produto:
    
    def __init__(self,
                 id: int,
                 nome: str,
                 diasDuraveis: int,
                 unidadeMedida: Union[UnidadeMedida, UnidadeConjunto]
                 ):
        
        '''
        está classe converte valores como 10.50 reais para 10500 milésimos de reais e 5 kg para 5000 gramas, garantindo precisão absoluta.
        se for um produto composto o i dicionario deve ter como chave o id do produto componente e valor quantidade em sua forma não formatada (int ou float)
        '''

        #verfiva se todos os parametros estão corretos
        if not isinstance(id, int) or id <= 0: raise ValueError(f"o id deve ser um numero inteiro positivo {id}")
        if not isinstance(nome, str) or nome == "": raise ValueError(f"o nome deve ser uma string {nome}")
        if not isinstance(diasDuraveis, int) or diasDuraveis <= 0: raise ValueError(f"a diasDuraveis deve ser um numero inteiro positivo {diasDuraveis}")
        if not isinstance(unidadeMedida, (UnidadeMedida, UnidadeConjunto)): raise ValueError(f"a unidadeMedida deve ser do tipo UnidadeMedida ou UnidadeConjunto {unidadeMedida}")
        
        #propriedade de identificação desse produto e sua caracteristicas
        self.__ID = id;
        self.__N = nome;
        self.__UM = unidadeMedida;
        self.__D = diasDuraveis;

        # valores de oprção recebido em momentos específicos
        self.__v = None;
        self.__q = None;
        self.__vu = None;
        self.__Receita = None;

        # propiedade de controle de dados do produto
        self.__valorTotal = 0;
        self.__estoque = 0;
        self.__valorTotalEstoque = 0;
    
        self.__quantidadeVendas = 0;
        self.__valorTotalVendas = 0;
        self.__valorTotalLucro = 0;


        

    def insertPropertValue(self, valorUnidario:float | str = None, quantidade:float | str = None, receita:dict | None = None) -> bool:
        # validar se os formatos de entrada estão corretos
        
        if not isinstance(valorUnidario, (int, float, str, type(None))): raise ValueError(f"o valorUnidario deve ser int ou float ou string {valorUnidario}")
        if not isinstance(quantidade, (int, float, str, type(None))): raise ValueError(f"a quantidade deve ser int ou float ou string {quantidade}")
        if not isinstance(receita, (dict, type(None))): raise ValueError(f"a receita deve ser um dict {receita}")

        # validar se oque estar entradando e instruções do produto compostos

        if (valorUnidario == None or quantidade == None) and receita != None:
            # validar se a receita é valida
            if self.__Receita == None:
                self.__Receita = receita;
                return self.__atualizarDados__();

            else:
                raise ValueError(f"este produto ja tem uma receita, não e possivel adicionar outra {self.__Receita}")
        
        elif self.__Receita != None:
            if valorUnidario is not None and quantidade is not None:
                try:
                    vu = MoedaReal.calculo_QeVp_Vu(self.__UM.getMultInt(), MoedaReal.parseCentavosPorMilhar(valorUnidario))
                    v = MoedaReal.parseCentavosPorMilhar(valorUnidario)
                    q = self.__UM.parseInt(quantidade)
                    self.__v = v
                    self.__q = q
                    self.__vu = vu
                    self.__atualizarDados__()
                    return True
                except Exception as e:
                    raise ValueError(f"erro ao converter valorUnidario ou quantidade: {e}")
            return self.__Receita
        
        else:

            try:

                vu = MoedaReal.calculo_QeVp_Vu(self.__UM.getMultInt(), MoedaReal.parseCentavosPorMilhar(valorUnidario));
                v = MoedaReal.parseCentavosPorMilhar(valorUnidario);
                q = self.__UM.parseInt(quantidade);

                if q < 0 : raise ValueError(f"a quantidade deve ser maior ou igual a 0 {q}")
                if v < 0: raise ValueError(f"o valor deve ser maior ou igual a 0 {v}")
                if vu < 0 : raise ValueError(f"o valor unitario deve ser maior ou igual a 0 {vu}")
                
            except Exception as e:
                raise ValueError(f"erro ao converter valorUnidario ou quantidade: {e}")

            
            #paramos aqui, ireimos mudar o campo de valor tirando do init e inserindo em um metodo proprior permitindo 
            # que a classe FictoryClassProduct fabricar essa classe sem precisar por valores na criaçao da instancia Produto
            
            self.__v = v;
            self.__q = q;
            self.__vu = vu;
            self.__Receita = receita;

            return self.__atualizarDados__();
            
        return False

    def alterarValores(self, instrucoes: dict) -> dict | bool:
        """
        Altera valores do produto (custo, quantidade total, acréscimo, decréscimo de estoque ou receita).
        Retorna um dicionário com os dados {'antes': dict, 'depois': dict} em caso de sucesso.
        Caso contrário, imprime o erro para a proteção de eficiência e retorna False.
        """
        if not isinstance(instrucoes, dict) or not instrucoes:
            print("Erro (Barreira): as instruções devem ser passadas como um dicionário não-vazio.")
            return False

        # 1. Barreira de Validação Rápida (Eficiência)
        valid_keys = {"valorUnidario", "quantidade", "quantidade_add", "quantidade_sub", "receita"}
        for k in instrucoes.keys():
            if k not in valid_keys:
                print(f"Erro (Barreira): chave '{k}' não é permitida para alteração.")
                return False
                
        if "receita" in instrucoes:
            if not isinstance(instrucoes["receita"], dict):
                print("Erro (Barreira): 'receita' deve ser um dicionário.")
                return False
            # Se for receita, proíbe misturar com alterações físicas na mesma requisição
            if any(k in instrucoes for k in ["valorUnidario", "quantidade", "quantidade_add", "quantidade_sub"]):
                print("Erro (Barreira): não é possível misturar alteração de receita com alteração física de estoque/custo.")
                return False

        for k in ["valorUnidario", "quantidade", "quantidade_add", "quantidade_sub"]:
            if k in instrucoes:
                if not isinstance(instrucoes[k], (int, float, str)):
                    print(f"Erro (Barreira): o valor de '{k}' deve ser numérico ou string. Obtido: {type(instrucoes[k])}")
                    return False

        # Guarda o estado atual (ANTES da mudança)
        estado_antes = self.getDados(f=True)

        try:
            # 2. Processamento (Somente executado se as barreiras iniciais passaram)
            if "receita" in instrucoes:
                self.__Receita = instrucoes["receita"]
                self.__atualizarDados__()
                return {"antes": estado_antes, "depois": self.getDados(f=True)}

            # Carrega valores atuais ou assume zero
            novo_v = self.__v
            novo_vu = self.__vu
            novo_q = self.__q if self.__q is not None else 0

            # Atualizar Valor Unitário de Custo
            if "valorUnidario" in instrucoes:
                novo_vu = MoedaReal.calculo_QeVp_Vu(self.__UM.getMultInt(), MoedaReal.parseCentavosPorMilhar(instrucoes["valorUnidario"]))
                novo_v = MoedaReal.parseCentavosPorMilhar(instrucoes["valorUnidario"])
                if novo_v < 0 or novo_vu < 0:
                    print("Erro (Lógica): valores financeiros (custo) não podem ser negativos.")
                    return False

            # Atualizar Quantidades (Atribuição direta, acréscimo ou decréscimo)
            if "quantidade" in instrucoes:
                novo_q = self.__UM.parseInt(instrucoes["quantidade"])
            
            if "quantidade_add" in instrucoes:
                novo_q += self.__UM.parseInt(instrucoes["quantidade_add"])

            if "quantidade_sub" in instrucoes:
                novo_q -= self.__UM.parseInt(instrucoes["quantidade_sub"])

            # Validação Final de Quantidade
            if novo_q < 0:
                print(f"Erro (Lógica): a quantidade em estoque não pode ficar negativa. Quantidade final seria: {self.__UM.parseFloat(novo_q)}")
                return False

            # 3. Efetivar Alterações
            self.__v = novo_v
            self.__vu = novo_vu
            self.__q = novo_q
            self.__Receita = None # Remove a receita caso o produto passe a ser de estoque físico

            self.__atualizarDados__()

            # Guarda o estado atualizado (DEPOIS da mudança)
            estado_depois = self.getDados(f=True)

            return {"antes": estado_antes, "depois": estado_depois}

        except Exception as e:
            print(f"Erro (Processamento): Falha ao tentar alterar e converter valores da instrução: {e}")
            return False

    def getDados(self, f:bool = False) -> dict:

        if not f or (self.__v == None and self.__q == None):
            if self.__Receita == None:
                dados = {
                    "id" : self.__ID,
                    "nome" : self.__N,
                    "UnidadeMedida" : self.__UM.getDescription(),
                    "diasDuraveis" : self.__D,

                    "valor" : self.__v,
                    "valorUnitario" : self.__vu,
                    "quantidadeEntrada" : self.__q,
                    "ValorTotal" : self.__valorTotal,
                    "estoque" : self.__estoque,
                    "valorTotalEstoque" : self.__valorTotalEstoque,
                    "vendas" : self.__quantidadeVendas,
                    "valorTotalVendas" : self.__valorTotalVendas,
                    "valorTotalLucro" : self.__valorTotalLucro
                }
            else: 
                dados = {
                    "id" : self.__ID,
                    "nome" : self.__N,
                    "UnidadeMedida" : self.__UM.getDescription(),
                    "diasDuraveis" : self.__D,
                    "Receita" : self.__Receita
                }
                if self.__v is not None:
                    dados.update({
                        "valor" : self.__v,
                        "valorUnitario" : self.__vu,
                        "quantidadeEntrada" : self.__q,
                        "ValorTotal" : self.__valorTotal,
                        "estoque" : self.__estoque,
                        "valorTotalEstoque" : self.__valorTotalEstoque,
                        "vendas" : self.__quantidadeVendas,
                        "valorTotalVendas" : self.__valorTotalVendas,
                        "valorTotalLucro" : self.__valorTotalLucro
                    })

        else:
            if self.__Receita == None:
                dados = {
                    "id" : self.__ID,
                    "nome" : self.__N,
                    "UnidadeMedida" : self.__UM.getDescription(),
                    "diasDuraveis" : self.__D,

                    "valor" : MoedaReal.parseMilharParaReais(self.__v),
                    "valorUnitario" : MoedaReal.parseMilharParaReais(self.__vu),
                    "quantidadeEntrada" : self.__UM.parseFloat(self.__q),
                    "ValorTotal" : MoedaReal.parseMilharParaReais(self.__valorTotal),
                    "estoque" : self.__UM.parseFloat(self.__estoque),
                    "valorTotalEstoque" : MoedaReal.parseMilharParaReais(self.__valorTotalEstoque),
                    "vendas" : self.__UM.parseFloat(self.__quantidadeVendas),
                    "valorTotalVendas" : MoedaReal.parseMilharParaReais(self.__valorTotalVendas),
                    "valorTotalLucro" : MoedaReal.parseMilharParaReais(self.__valorTotalLucro)
                }
            else: 
                dados = {
                    "id" : self.__ID,
                    "nome" : self.__N,
                    "UnidadeMedida" : self.__UM.getDescription(),
                    "diasDuraveis" : self.__D,
                    "Receita" : self.__Receita
                }
                if self.__v is not None:
                    dados.update({
                        "valor" : MoedaReal.parseMilharParaReais(self.__v),
                        "valorUnitario" : MoedaReal.parseMilharParaReais(self.__vu),
                        "quantidadeEntrada" : self.__UM.parseFloat(self.__q),
                        "ValorTotal" : MoedaReal.parseMilharParaReais(self.__valorTotal),
                        "estoque" : self.__UM.parseFloat(self.__estoque),
                        "valorTotalEstoque" : MoedaReal.parseMilharParaReais(self.__valorTotalEstoque),
                        "vendas" : self.__UM.parseFloat(self.__quantidadeVendas),
                        "valorTotalVendas" : MoedaReal.parseMilharParaReais(self.__valorTotalVendas),
                        "valorTotalLucro" : MoedaReal.parseMilharParaReais(self.__valorTotalLucro)
                    })

        return dados
    
    def __atualizarDados__(self) -> bool:

        if  self.__Receita != None: 
            for key in self.__Receita.keys():
                if not isinstance(key, int): raise ValueError(f"a key do dict deve ser int {key}")
                if not isinstance(self.__Receita[key], int | float): raise ValueError(f"o valor do dict deve ser int {self.__Receita[key]}")

            return True
           
        self.__valorTotal = MoedaReal.calculo_PQV_T(self.__UM.getMultInt(), self.__q, self.__v)
        self.__estoque = self.__q - self.__quantidadeVendas
        self.__valorTotalEstoque = MoedaReal.calculo_PQV_T(self.__UM.getMultInt(), self.__estoque, self.__v)
        
        return True
        

    def vender(self, quantidadeVendas : float | str = None, valorVenda : float | str = None) -> dict:

        if self.__v == None and self.__Receita != None: return self.__Receita

        if quantidadeVendas == None or valorVenda == None : 
            raise ValueError(f"o campo quantidadeVendas e valorVenda não podem ser nulos {quantidadeVendas} {valorVenda}")
        

        try:

            q = self.__UM.parseInt(quantidadeVendas);

            if self.__Receita == None and q > self.__estoque: raise ValueError(f"Quantidade {q} maior que estoque {self.__estoque}")

            vv = MoedaReal.parseCentavosPorMilhar(valorVenda);
            

            total = MoedaReal.calculo_PQV_T(self.__UM.getMultInt(), q, vv);
            custo = MoedaReal.calculo_PQV_T(self.__UM.getMultInt(), q, self.__v);
            lucro = total - custo; 

        except Exception as e:
            raise ValueError(f"erro ao calcular a venda: {e}");
           



        self.__quantidadeVendas += q;
        self.__valorTotalVendas += total;
        self.__valorTotalLucro  += lucro;

        self.__atualizarDados__()

        return {
            "id" : self.__ID,
            "nome" : self.__N,
            "UnidadeMedida" : self.__UM.getDescription(),
            "itemVendidos" : self.__UM.parseFloat(q),
            "CustoUnitario" : MoedaReal.parseMilharParaReais(self.__v),
            "valorCustoTotal" : MoedaReal.parseMilharParaReais(custo),
            "valorVendaUnitario" : MoedaReal.parseMilharParaReais(vv),
            "valorVendaTotal" : MoedaReal.parseMilharParaReais(total),
            "lucroTotal" : MoedaReal.parseMilharParaReais(lucro)
        }





















if False:
    # 1. Teste com KG (Kilograma)
    p_kg = Produto(
        id=1,
        nome="Arroz Integral",
        diasDuraveis=180,
        unidadeMedida=UnidadeMedida.KG
    )
    p_kg.insertPropertValue(valorUnidario="5.50", quantidade="10.5") # 10.5 kg a 5.50/kg
    print("--- Teste Produto KG ---")
    for k, v in p_kg.getDados(f=True).items():
        print(f"{k} ==> {v}")
    p_kg.vender("2.5", "8.00") # Vende 2.5 kg a 8.00/kg
    print("\nDepois da venda de 2.5 kg:")
    for k, v in p_kg.getDados(f=True).items():
        print(f"{k} ==> {v}")
    print("-" * 50)

    # 2. Teste com L (Litros)
    p_l = Produto(
        id=2,
        nome="Leite Integral",
        diasDuraveis=10,
        unidadeMedida=UnidadeMedida.L
    )
    p_l.insertPropertValue(valorUnidario="4.20", quantidade="20") # 20 litros a 4.20/L
    print("\n--- Teste Produto L ---")
    for k, v in p_l.getDados(f=True).items():
        print(f"{k} ==> {v}")
    p_l.vender("5.5", "6.00") # Vende 5.5 litros a 6.00/L
    print("\nDepois da venda de 5.5 L:")
    for k, v in p_l.getDados(f=True).items():
        print(f"{k} ==> {v}")
    print("-" * 50)

    # 3. Teste com UNIDADE (Unidade)
    p_un = Produto(
        id=3,
        nome="Sabonete Líquido",
        diasDuraveis=365,
        unidadeMedida=UnidadeMedida.UNIDADE
    )
    p_un.insertPropertValue(valorUnidario="12.00", quantidade="50") # 50 unidades a 12.00/un
    print("\n--- Teste Produto UNIDADE ---")
    for k, v in p_un.getDados(f=True).items():
        print(f"{k} ==> {v}")
    p_un.vender("10", "15.50") # Vende 10 unidades a 15.50/un
    print("\nDepois da venda de 10 unidades:")
    for k, v in p_un.getDados(f=True).items():
        print(f"{k} ==> {v}")
    print("-" * 50)

    # 4. Teste com Unidade de Conjunto (UnidadeConjunto)
    p_conj = Produto(
        id=4,
        nome="Fardo de Coca-Cola 350ml",
        diasDuraveis=120,
        unidadeMedida=UnidadeConjunto(UnidadeMedida.CONJUNTO, 6) # Conjunto de 6 unidades
    )
    p_conj.insertPropertValue(valorUnidario="30.00", quantidade="10") # 10 fardos a 30.00/fardo
    print("\n--- Teste Produto CONJUNTO ---")
    for k, v in p_conj.getDados(f=True).items():
        print(f"{k} ==> {v}")
    p_conj.vender("3", "38.00") # Vende 3 fardos a 38.00/fardo
    print("\nDepois da venda de 3 fardos:")
    for k, v in p_conj.getDados(f=True).items():
        print(f"{k} ==> {v}")
    print("-" * 50)




    p = Produto(11,"cx ovo",30, UnidadeMedida.UNIDADE)
    p.insertPropertValue(valorUnidario=14.5, quantidade=60)

    print("\n--- ANTES DA ALTERAÇÃO ---")
    for k, v in p.getDados(f=True).items():
        print(f"{k} ==> {v}")

    # Testa o novo método de alteração com dicionário
    resultado_alteracao = p.alterarValores({
        "quantidade_add": 20,         # Soma 20 no estoque (Total de 80)
        "valorUnidario": 15.00        # Aumenta o custo para 15.00
    })

    if resultado_alteracao:
        print("\n--- ALTERAÇÃO BEM SUCEDIDA ---")
        print("ESTADO ANTES:")
        for k, v in resultado_alteracao["antes"].items():
            print(f"  {k}: {v}")
        print("\nESTADO DEPOIS:")
        for k, v in resultado_alteracao["depois"].items():
            print(f"  {k}: {v}")
    else:
        print("\n--- FALHA NA ALTERAÇÃO ---")