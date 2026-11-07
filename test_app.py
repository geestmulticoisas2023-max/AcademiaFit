import os
import tempfile
import unittest
import app as projeto

class AcademiaFitTests(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        projeto.DB_PATH = self.path
        projeto.app.config['TESTING'] = True
        projeto.init_db()
        self.client = projeto.app.test_client()

    def tearDown(self):
        os.unlink(self.path)

    def test_01_painel_inicial(self):
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_02_cadastro_aluno(self):
        r = self.client.post('/alunos', data={'nome':'Aluno Teste','email':'teste@example.com','telefone':'11999999999'}, follow_redirects=True)
        self.assertIn(b'Aluno Teste', r.data)

    def test_03_validacao_cadastro(self):
        self.client.post('/alunos', data={'nome':'','email':'invalido','telefone':''})
        with projeto.connection() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM alunos').fetchone()[0], 0)

    def test_04_registro_mensalidade(self):
        self.client.post('/alunos', data={'nome':'Aluno Teste','email':'teste@example.com','telefone':'11999999999'})
        r = self.client.post('/mensalidades', data={'aluno_id':'1','competencia':'2026-11','valor':'99.90'}, follow_redirects=True)
        self.assertIn(b'Pendente', r.data)

    def test_05_consulta_pendencia_e_pagamento(self):
        self.client.post('/alunos', data={'nome':'Aluno Teste','email':'teste@example.com','telefone':'11999999999'})
        self.client.post('/mensalidades', data={'aluno_id':'1','competencia':'2026-11','valor':'99.90'})
        self.assertIn(b'Aluno Teste', self.client.get('/pendencias').data)
        self.client.post('/mensalidades/1/pagar')
        self.assertNotIn(b'Aluno Teste', self.client.get('/pendencias').data)

if __name__ == '__main__':
    unittest.main()
