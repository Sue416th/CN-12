import fetch from 'fetch';

async function register() {
  const response = await fetch('http://127.0.0.1:3001/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: '测试用户',
      email: 'test@example.com',
      password: '123456',
      role: 'user'
    })
  });
  const data = await response.json();
  console.log(JSON.stringify(data, null, 2));
}

register();
