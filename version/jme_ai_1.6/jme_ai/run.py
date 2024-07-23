from app import create_app

# Cria uma instância da aplicação Flask
app = create_app()

# Executa a aplicação se este arquivo for o ponto de entrada principal
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
