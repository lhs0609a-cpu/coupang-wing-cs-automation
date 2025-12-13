// Vercel 환경 변수 업데이트 스크립트
const https = require('https');
const fs = require('fs');

// .env.vercel에서 VERCEL_OIDC_TOKEN 읽기
const envContent = fs.readFileSync('.env.vercel', 'utf8');
const tokenMatch = envContent.match(/VERCEL_OIDC_TOKEN="([^"]+)"/);
const token = tokenMatch ? tokenMatch[1] : null;

if (!token) {
  console.error('VERCEL_OIDC_TOKEN을 찾을 수 없습니다.');
  process.exit(1);
}

const projectId = 'prj_CrSD7t4KCJXxY3ED3xt2WE65YAxa';
const teamId = 'team_k3YzonQpYYM8VgPAMI31SaUB';

// 먼저 기존 환경 변수 ID 조회
const getEnvOptions = {
  hostname: 'api.vercel.com',
  path: `/v9/projects/${projectId}/env?teamId=${teamId}`,
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
};

console.log('기존 환경 변수 조회 중...');

const getReq = https.request(getEnvOptions, (res) => {
  let data = '';

  res.on('data', (chunk) => {
    data += chunk;
  });

  res.on('end', () => {
    try {
      const envVars = JSON.parse(data);
      const viteApiUrl = envVars.envs?.find(env => env.key === 'VITE_API_URL' && env.target?.includes('production'));

      if (viteApiUrl) {
        console.log(`기존 VITE_API_URL 발견: ${viteApiUrl.id}`);

        // 기존 환경 변수 삭제
        const deleteOptions = {
          hostname: 'api.vercel.com',
          path: `/v9/projects/${projectId}/env/${viteApiUrl.id}?teamId=${teamId}`,
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        };

        console.log('기존 환경 변수 삭제 중...');

        const deleteReq = https.request(deleteOptions, (delRes) => {
          let delData = '';

          delRes.on('data', (chunk) => {
            delData += chunk;
          });

          delRes.on('end', () => {
            console.log('삭제 완료. 새 환경 변수 추가 중...');
            addNewEnvVar();
          });
        });

        deleteReq.on('error', (e) => {
          console.error(`삭제 중 오류: ${e.message}`);
          process.exit(1);
        });

        deleteReq.end();
      } else {
        console.log('기존 VITE_API_URL을 찾지 못했습니다. 새로 추가합니다.');
        addNewEnvVar();
      }
    } catch (e) {
      console.error('응답 파싱 오류:', e.message);
      console.error('응답 데이터:', data);
      process.exit(1);
    }
  });
});

getReq.on('error', (e) => {
  console.error(`조회 중 오류: ${e.message}`);
  process.exit(1);
});

getReq.end();

function addNewEnvVar() {
  const postData = JSON.stringify({
    key: 'VITE_API_URL',
    value: 'https://coupang-wing-cs-backend.fly.dev',
    type: 'plain',
    target: ['production']
  });

  const options = {
    hostname: 'api.vercel.com',
    path: `/v10/projects/${projectId}/env?teamId=${teamId}`,
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(postData)
    }
  };

  const req = https.request(options, (res) => {
    let responseData = '';

    res.on('data', (chunk) => {
      responseData += chunk;
    });

    res.on('end', () => {
      if (res.statusCode === 200 || res.statusCode === 201) {
        console.log('환경 변수가 성공적으로 추가되었습니다!');
        console.log('응답:', responseData);
      } else {
        console.error(`오류 (${res.statusCode}):`, responseData);
        process.exit(1);
      }
    });
  });

  req.on('error', (e) => {
    console.error(`요청 중 오류: ${e.message}`);
    process.exit(1);
  });

  req.write(postData);
  req.end();
}
