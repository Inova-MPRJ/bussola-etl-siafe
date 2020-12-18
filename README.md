# Extrair, transformar e carregar dados do SIAFE-Rio _(bussola-etl-siafe)_

Extrair, transformar e carregar dados do Sistema Integrado de Gestão Orçamentária, Financeira e Contábil do Estado do Rio de Janeiro (SIAFE-Rio).

SIAFE-Rio é o Sistema Integrado de Gestão Orçamentária, Financeira e Contábil do Rio de Janeiro, que consiste no principal instrumento utilizado para registro,  companhamento e controle da execução orçamentária, financeira e patrimonial do Governo do Estado do Rio de Janeiro.

Este pacote contém ferramentas para interagir de forma automatizada com a
interface web do sistema SIAFE-Rio.

## Índice

- [Instalação](#instalacao)
- [Uso](#uso)

## Instalação

A instalação pode ser realizada diretamente a partir do repositório utilizando a ferramenta  `pip` em um ambiente virtual apropriado, ou com uma alternativa que gerencie o isolamento de ambientes nativamente, como o `pipx`.

Em sistemas Unix ou MacOS:

```sh
python3 -m venv my-env
source my-env/bin/activate
pip install python -m pip install git+https://github.com/inova-mprj/bussola-etl-siafe
```

No Windows:

```sh
python3 -m venv my-env
my-env\Scripts\activate.bat
pip install python -m pip install git+https://github.com/inova-mprj/bussola-etl-siafe
```

Ou, utilizando o `pipx` (Windows, Unix e MacOS):
```sh
pipx install git+https://github.com/inova-mprj/bussola-etl-siafe
```

Você também pode adicionar o pacote como dependência de outra aplicação Python,utilizando um gerenciador de dependências como o `pipenv` ou o `poetry`.

```sh
# com Pipenv
pipenv add git+https://github.com/inova-mprj/bussola-etl-siafe

# com Poetry
poetry add git+https://github.com/inova-mprj/bussola-etl-siafe
```

### Instalando o ChromeDriver

Este pacote utiliza a ferramenta de automatização de testes [Selenium](https://www.selenium.dev/) para interagir com a aplicação web do SIAFE-Rio.

Para utilizar o Selenium, você precisa de uma versão mínima do navegador Chrome (ChromeDriver), que pode ser baixada [aqui](https://sites.google.com/a/chromium.org/chromedriver/downloads).

Salve o arquivo e descompacte em um local de fácil acesso. A localização do arquivo executável descompactado precisa ser passada como um parâmetro ao estabelecer uma nova conexão com o sistema (veja [abaixo](#uso)).

Adicionalmente, pode ser necessário instalar alguns pacotes adicionais no seu computador para que o ChromeDriver funcione da maneira esperada. Em distribuições Unix baseadas em Debian, você pode instalar essas dependências com o comando (pode ser necessário rodar com privilégios de superusuário, `sudo`):

```sh
sudo apt-get install -y chromium-driver \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 
```

## Uso

Para criar uma conexão com o Módulo Básico do SIAFE-Rio, importe a classe `bussola_etl_siafe.siafe.SiafeClient` e crie uma nova conexão com as suas credenciais de acesso ao sistema. O objeto criado possui uma propriedade `driver`, que possui os mesmos métodos da classe [`WebDriver` do Selenium](https://selenium-python.readthedocs.io/api.html#module-selenium.webdriver.chrome.webdriver).

O exemplo a seguir cria uma nova conexão utilizando credenciais hipotéticas e 
reproduz a mensagem de boas-vindas presente no sistema.

```python
from bussola_etl_siafe.siafe import SiafeClient

siafe = SiafeClient(
    user='01010101010',
    password='my-secret-passwd',
    driver_path = '~/chromedriver'
)

driver = siafe.driver

# Diga olá!
greetings = driver.greet()
print(greetings)
```

## Mantenedor

Este pacote é mantido pela equipe do [Laboratório de Inovação do Ministério Público do Estado do Rio de Janeiro](http://www.mprj.mp.br/inova) (Inova_MPRJ), como parte do projeto [Bússola](https://github.com/Inova-MPRJ/bussola).

## Como contribuir

Você pode contribuir com dúvidas, sugestões e comentários na seção [Issues do repositório](https://github.com/Inova-MPRJ/bussola-etl-siafe/issues). Melhorias podem ser enviadas como [Pull Requests](https://github.com/Inova-MPRJ/bussola-etl-siafe/pulls), e serão revisadas pela equipe do Inova_MPRJ.

Qualquer que seja o caso, esteja atenta(o) ao nosso [Código de Conduta](https://www.contributor-covenant.org/pt-br/version/2/0/code_of_conduct/).

## Licença

Copyright 2020 Ministério Público do Estado do Rio de Janeiro

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.