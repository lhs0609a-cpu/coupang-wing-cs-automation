import React, { useState, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import {
  Search,
  RefreshCw,
  ExternalLink,
  Copy,
  Package,
  Calendar,
  CheckCircle,
  AlertCircle,
  Loader2,
  ShoppingCart,
  X,
  TrendingDown,
  Store,
  ArrowUpDown
} from 'lucide-react'
import { getApiBaseUrl } from '../utils/apiConfig'
import '../styles/ProductSearch.css'

const SHEET_ID = '1wBxJlm1_p3BJAi16hcgw0XxlnW4Fquk_gfm9dtE4QR0'
const CSV_URL = `https://docs.google.com/spreadsheets/d/${SHEET_ID}/export?format=csv`

const ProductSearch = ({ showNotification }) => {
  const [products, setProducts] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(false)
  const [lastSync, setLastSync] = useState(null)
  const [error, setError] = useState(null)
  const [copiedId, setCopiedId] = useState(null)

  // 가격 비교 관련 상태
  const [priceCompareLoading, setPriceCompareLoading] = useState(null)
  const [priceCompareResults, setPriceCompareResults] = useState(null)
  const [selectedProduct, setSelectedProduct] = useState(null)
  const [extractedProductName, setExtractedProductName] = useState(null)
  const [extractSource, setExtractSource] = useState(null)
  const [sortOrder, setSortOrder] = useState('asc') // 가격 낮은순

  const apiBaseUrl = getApiBaseUrl()

  // CSV 파싱 함수
  const parseCSV = (csvText) => {
    const lines = csvText.split('\n')
    const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''))

    const data = []
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i]
      if (!line.trim()) continue

      // CSV 파싱 (쉼표가 포함된 필드 처리)
      const values = []
      let current = ''
      let inQuotes = false

      for (let j = 0; j < line.length; j++) {
        const char = line[j]
        if (char === '"') {
          inQuotes = !inQuotes
        } else if (char === ',' && !inQuotes) {
          values.push(current.trim().replace(/"/g, ''))
          current = ''
        } else {
          current += char
        }
      }
      values.push(current.trim().replace(/"/g, ''))

      if (values.length >= 3) {
        // 이미지 URL 찾기 (상품명 다음 컬럼들 중 이미지 URL로 보이는 것)
        let imageUrl = ''
        for (let k = 2; k < values.length; k++) {
          const val = values[k] || ''
          // 이미지 URL 패턴 확인 (jpg, png, gif, webp 등)
          if (val.match(/\.(jpg|jpeg|png|gif|webp)/i) ||
              val.includes('image') ||
              val.includes('img') ||
              val.includes('thumbnail') ||
              val.includes('cdn')) {
            imageUrl = val
            break
          }
        }

        // URL 찾기 (쿠팡, 11번가, 네이버 등 쇼핑몰 URL)
        let productUrl = ''
        for (let k = 2; k < values.length; k++) {
          const val = values[k] || ''
          if (val.includes('coupang.com') ||
              val.includes('11st.co.kr') ||
              val.includes('naver.com') ||
              val.includes('gmarket') ||
              val.includes('auction') ||
              val.startsWith('http')) {
            // 이미지 URL이 아닌 경우에만
            if (!val.match(/\.(jpg|jpeg|png|gif|webp)/i)) {
              productUrl = val
              break
            }
          }
        }

        data.push({
          id: values[0] || '',
          name: values[1] || '',
          image: imageUrl,
          url: productUrl || values[2] || '',
          date: values[values.length - 1] || values[3] || ''
        })
      }
    }

    return data
  }

  // Google Sheets에서 데이터 가져오기
  const fetchProducts = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(CSV_URL)
      if (!response.ok) throw new Error('데이터를 가져올 수 없습니다')

      const csvText = await response.text()
      const data = parseCSV(csvText)

      setProducts(data)
      setLastSync(new Date())
      localStorage.setItem('productSearchData', JSON.stringify(data))
      localStorage.setItem('productSearchLastSync', new Date().toISOString())

      if (showNotification) {
        showNotification(`${data.length}개 상품 동기화 완료`, 'success')
      }
    } catch (err) {
      console.error('Fetch error:', err)
      setError('Google Sheets 연동 실패. 잠시 후 다시 시도해주세요.')

      // 캐시된 데이터 사용
      const cached = localStorage.getItem('productSearchData')
      if (cached) {
        setProducts(JSON.parse(cached))
        const cachedTime = localStorage.getItem('productSearchLastSync')
        if (cachedTime) setLastSync(new Date(cachedTime))
      }
    } finally {
      setLoading(false)
    }
  }

  // 초기 로드
  useEffect(() => {
    const cached = localStorage.getItem('productSearchData')
    const cachedTime = localStorage.getItem('productSearchLastSync')

    if (cached) {
      setProducts(JSON.parse(cached))
      if (cachedTime) setLastSync(new Date(cachedTime))
    }

    // 캐시가 1시간 이상 지났으면 자동 새로고침
    if (!cachedTime || Date.now() - new Date(cachedTime).getTime() > 3600000) {
      fetchProducts()
    }
  }, [])

  // 검색 필터링
  const filteredProducts = useMemo(() => {
    if (!searchTerm.trim()) return []

    const term = searchTerm.toLowerCase()
    return products.filter(p =>
      p.id.toLowerCase().includes(term) ||
      p.name.toLowerCase().includes(term)
    ).slice(0, 50) // 최대 50개 결과
  }, [products, searchTerm])

  // URL 열기
  const openProductUrl = (url) => {
    if (url) {
      window.open(url, '_blank')
    }
  }

  // 복사
  const copyToClipboard = async (product) => {
    const text = `${product.id}\n${product.name}\n${product.url}`
    try {
      await navigator.clipboard.writeText(text)
      setCopiedId(product.id)
      setTimeout(() => setCopiedId(null), 2000)
      if (showNotification) {
        showNotification('클립보드에 복사되었습니다', 'success')
      }
    } catch (err) {
      console.error('Copy failed:', err)
    }
  }

  // 날짜 포맷
  const formatDate = (dateStr) => {
    if (!dateStr) return ''
    return dateStr.replace('오전', 'AM').replace('오후', 'PM')
  }

  // 가격 포맷
  const formatPrice = (price) => {
    const num = parseInt(price) || 0
    return num.toLocaleString('ko-KR') + '원'
  }

  // 네이버 쇼핑 가격 비교 검색
  const searchPriceCompare = async (product, useExtractedName = null) => {
    setPriceCompareLoading(product.id)
    setSelectedProduct(product)
    setPriceCompareResults(null)

    try {
      let searchQuery = useExtractedName

      // 추출된 상품명이 없으면 URL에서 추출 시도
      if (!searchQuery && product.url) {
        if (showNotification) {
          showNotification('상품 페이지에서 상품명 추출 중...', 'success')
        }

        const extractResponse = await axios.get(`${apiBaseUrl}/naver-shopping/extract-product-name`, {
          params: { url: product.url }
        })

        if (extractResponse.data.success && extractResponse.data.product_name) {
          searchQuery = extractResponse.data.product_name
          setExtractedProductName(searchQuery)
          setExtractSource(extractResponse.data.source)
          if (showNotification) {
            showNotification(`${extractResponse.data.source}에서 상품명 추출 완료`, 'success')
          }
        } else {
          // 추출 실패 시 기존 상품명 사용
          searchQuery = product.name
          setExtractedProductName(null)
          setExtractSource(null)
          if (showNotification) {
            showNotification('상품명 추출 실패, 기존 상품명으로 검색합니다', 'error')
          }
        }
      }

      // 네이버 쇼핑 검색
      const response = await axios.get(`${apiBaseUrl}/naver-shopping/search`, {
        params: {
          query: searchQuery,
          display: 30,
          sort: sortOrder
        }
      })

      setPriceCompareResults(response.data)
      if (showNotification) {
        showNotification(`${response.data.items.length}개 판매처 검색 완료`, 'success')
      }
    } catch (err) {
      console.error('Price compare error:', err)
      if (showNotification) {
        showNotification('가격 비교 검색 실패', 'error')
      }
    } finally {
      setPriceCompareLoading(null)
    }
  }

  // 가격 비교 모달 닫기
  const closePriceCompare = () => {
    setPriceCompareResults(null)
    setSelectedProduct(null)
    setExtractedProductName(null)
    setExtractSource(null)
  }

  // 정렬 변경
  const toggleSortOrder = () => {
    const newOrder = sortOrder === 'asc' ? 'dsc' : 'asc'
    setSortOrder(newOrder)
    if (selectedProduct && extractedProductName) {
      // 이미 추출된 상품명이 있으면 그걸로 재검색
      searchPriceCompare(selectedProduct, extractedProductName)
    }
  }

  return (
    <div className="product-search">
      <div className="product-search-header">
        <div>
          <h1 className="product-search-title">상품 검색</h1>
          <p className="product-search-subtitle">
            Google Sheets 연동 ({products.length.toLocaleString()}개 상품)
          </p>
        </div>
        <button
          className={`sync-button ${loading ? 'loading' : ''}`}
          onClick={fetchProducts}
          disabled={loading}
        >
          {loading ? <Loader2 size={18} className="spin" /> : <RefreshCw size={18} />}
          <span>{loading ? '동기화 중...' : '동기화'}</span>
        </button>
      </div>

      {lastSync && (
        <div className="last-sync">
          <Calendar size={14} />
          <span>마지막 동기화: {lastSync.toLocaleString('ko-KR')}</span>
        </div>
      )}

      {error && (
        <div className="error-banner">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      <div className="search-container">
        <div className="search-input-wrapper">
          <Search size={20} className="search-icon" />
          <input
            type="text"
            className="search-input"
            placeholder="상품고유번호 또는 상품명 입력... (예: 11ST-5d99a506...)"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            autoFocus
          />
          {searchTerm && (
            <button
              className="clear-button"
              onClick={() => setSearchTerm('')}
            >
              ✕
            </button>
          )}
        </div>
      </div>

      <div className="search-results">
        {searchTerm && filteredProducts.length === 0 && !loading && (
          <div className="no-results">
            <Package size={48} />
            <p>검색 결과가 없습니다</p>
            <span>다른 검색어를 입력해보세요</span>
          </div>
        )}

        <AnimatePresence>
          {filteredProducts.map((product, index) => (
            <motion.div
              key={product.id}
              className="product-card"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ delay: index * 0.05 }}
            >
              {/* 상품 대표 이미지 */}
              <div className="product-thumbnail">
                {product.image ? (
                  <img
                    src={product.image}
                    alt={product.name}
                    onError={(e) => {
                      e.target.style.display = 'none'
                      e.target.nextSibling.style.display = 'flex'
                    }}
                  />
                ) : null}
                <div className="product-thumbnail-placeholder" style={{ display: product.image ? 'none' : 'flex' }}>
                  <Package size={32} />
                </div>
              </div>

              <div className="product-info">
                <div className="product-name">
                  <span>{product.name || '상품명 없음'}</span>
                </div>
                <div className="product-id">
                  <code>{product.id}</code>
                </div>
                {product.date && (
                  <div className="product-date">
                    <Calendar size={14} />
                    <span>{formatDate(product.date)}</span>
                  </div>
                )}
              </div>

              <div className="product-actions">
                <button
                  className="action-button compare"
                  onClick={() => searchPriceCompare(product)}
                  disabled={priceCompareLoading === product.id}
                  title="네이버 쇼핑 가격 비교"
                >
                  {priceCompareLoading === product.id ? (
                    <>
                      <Loader2 size={18} className="spin" />
                      <span>검색중...</span>
                    </>
                  ) : (
                    <>
                      <TrendingDown size={18} />
                      <span>가격 비교</span>
                    </>
                  )}
                </button>
                <button
                  className="action-button primary"
                  onClick={() => openProductUrl(product.url)}
                  title="상품 페이지 열기"
                >
                  <ExternalLink size={18} />
                  <span>상품 페이지</span>
                </button>
                <button
                  className={`action-button ${copiedId === product.id ? 'copied' : ''}`}
                  onClick={() => copyToClipboard(product)}
                  title="복사"
                >
                  {copiedId === product.id ? (
                    <>
                      <CheckCircle size={18} />
                      <span>복사됨</span>
                    </>
                  ) : (
                    <>
                      <Copy size={18} />
                      <span>복사</span>
                    </>
                  )}
                </button>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {!searchTerm && (
          <div className="search-hint">
            <Search size={48} />
            <p>상품을 검색해보세요</p>
            <span>상품고유번호(11ST-...) 또는 상품명으로 검색할 수 있습니다</span>
          </div>
        )}
      </div>

      {/* 가격 비교 모달 */}
      <AnimatePresence>
        {priceCompareResults && selectedProduct && (
          <motion.div
            className="price-compare-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closePriceCompare}
          >
            <motion.div
              className="price-compare-modal"
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="price-compare-header">
                <div className="price-compare-title">
                  <ShoppingCart size={24} />
                  <div>
                    <h2>네이버 쇼핑 가격 비교</h2>
                    <p>{extractedProductName || selectedProduct.name}</p>
                    {extractSource && (
                      <span className="extract-source">({extractSource}에서 추출)</span>
                    )}
                  </div>
                </div>
                <div className="price-compare-controls">
                  <button
                    className="sort-button"
                    onClick={toggleSortOrder}
                  >
                    <ArrowUpDown size={18} />
                    <span>{sortOrder === 'asc' ? '가격 낮은순' : '가격 높은순'}</span>
                  </button>
                  <button className="close-button" onClick={closePriceCompare}>
                    <X size={24} />
                  </button>
                </div>
              </div>

              <div className="price-compare-info">
                <span>총 {priceCompareResults.total.toLocaleString()}개 검색 / {priceCompareResults.items.length}개 표시</span>
              </div>

              <div className="price-compare-list">
                {priceCompareResults.items.map((item, index) => (
                  <motion.div
                    key={item.productId + index}
                    className={`price-item ${index === 0 ? 'best-price' : ''}`}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.03 }}
                  >
                    {index === 0 && (
                      <div className="best-badge">최저가</div>
                    )}
                    <div className="price-item-image">
                      {item.image ? (
                        <img src={item.image} alt={item.title} />
                      ) : (
                        <div className="no-image">
                          <Package size={24} />
                        </div>
                      )}
                    </div>
                    <div className="price-item-info">
                      <div className="price-item-title">{item.title}</div>
                      <div className="price-item-meta">
                        <span className="mall-name">
                          <Store size={14} />
                          {item.mallName}
                        </span>
                        {item.brand && (
                          <span className="brand">{item.brand}</span>
                        )}
                        {item.category1 && (
                          <span className="category">{item.category1}</span>
                        )}
                      </div>
                    </div>
                    <div className="price-item-price">
                      <div className="main-price">{formatPrice(item.lprice)}</div>
                      {item.hprice && item.hprice !== '0' && item.hprice !== item.lprice && (
                        <div className="range-price">~ {formatPrice(item.hprice)}</div>
                      )}
                    </div>
                    <button
                      className="buy-button"
                      onClick={() => window.open(item.link, '_blank')}
                    >
                      <ShoppingCart size={16} />
                      <span>구매하기</span>
                    </button>
                  </motion.div>
                ))}

                {priceCompareResults.items.length === 0 && (
                  <div className="no-price-results">
                    <Package size={48} />
                    <p>검색 결과가 없습니다</p>
                    <span>다른 상품명으로 검색해보세요</span>
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default ProductSearch
