import React from 'react';
import { Layout, Menu } from 'antd';
import { ThunderboltTwoTone, ExperimentTwoTone } from '@ant-design/icons';
import { Route, Routes, Link, Navigate, useLocation } from 'react-router-dom';
import InferencePage from 'page/inference/InferencePage';
import TrainPage from 'page/train/TrainPage';
import './Dashboard.css';

const { Header, Sider, Content } = Layout;

function Dashboard() {
  const menuItems = [
    {
      key: '/inference',
      icon: <ThunderboltTwoTone />,
      label: <Link to="/inference">추론</Link>
    },
    {
      key: '/train',
      icon: <ExperimentTwoTone />,
      label: <Link to="/train">데이터 학습/배포</Link>
    },
  ];

  const location = useLocation();
  const getHeaderTitle = () => {
    const menuName = menuItems.filter((munuItem) => munuItem.key === location.pathname)[0]?.label?.props?.children;
    if (!menuName) {
        return '대시보드';
    }
    return `${menuName}`;
  };

  return (
      <Layout style={{ minHeight: '100vh' }} className='navbar_frame'>
        {/* 좌측 사이드바 */}
        <Sider
          width={200}
          style={{
            background: '#fff',
          }}
        >
          {/* 로고 추가 */}
          <div
            style={{
              height: '64px',
              textAlign: 'center',
              lineHeight: '64px',
              fontSize: '23px',
              fontWeight: 'bold',
            }}
          >
            WATCH ML
          </div>
          <Menu
            mode="inline"
            defaultSelectedKeys={['/monitoring']}
            selectedKeys={[location.pathname]}
            items={menuItems}
            style={{
              height: '100%',
              borderRight: 0,
              fontSize: '12px',
            }}
          />
        </Sider>
        <Layout style={{ padding: '0 24px 24px',minHeight: '100vh'}} className="page_frame">
          <Header
            style={{
              background: '#fff',
              padding: 0,
              fontSize: '13px',
              color: '#555',
              fontWeight: 'bold'
            }}
          >
              {getHeaderTitle()}
          </Header>
          <Content
            style={{
              padding: 24,
              margin: 0,
              minHeight: 280,
              background: '#fff',
            }}
          >
            <Routes>
              <Route path="/" element={<Navigate to="/inference" />} />
              <Route path="/inference" element={<InferencePage />} />
              <Route path="/train" element={<TrainPage />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
  );
}

export default Dashboard;
