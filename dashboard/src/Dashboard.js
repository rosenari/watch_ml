import React from 'react';
import { Layout, Menu } from 'antd';
import { VideoCameraOutlined, BarChartOutlined } from '@ant-design/icons';
import { Route, Routes, Link, Navigate, useLocation } from 'react-router-dom';
import MonitoringPage from './page/MonitoringPage';
import DeploymentPage from './page/DeploymentPage';
import './Dashboard.css';

const { Header, Sider, Content } = Layout;

function Dashboard() {
  const menuItems = [
    {
      key: '/monitoring',
      icon: <VideoCameraOutlined />,
      label: <Link to="/monitoring">모니터링</Link>
    },
    {
      key: '/deployment',
      icon: <BarChartOutlined />,
      label: <Link to="/deployment">데이터 학습/배포</Link>
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
              fontSize: '16px',
              fontWeight: 'bold',
            }}
          >
            교통 모니터링 시스템
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
              <Route path="/" element={<Navigate to="/monitoring" />} />
              <Route path="/monitoring" element={<MonitoringPage />} />
              <Route path="/deployment" element={<DeploymentPage />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
  );
}

export default Dashboard;
