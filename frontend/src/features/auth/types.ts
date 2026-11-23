/** Kết quả đăng nhập bệnh nhân (FR-TK-01); tên trường theo backend app/modules/auth/schemas.py. */
export interface LoginResult {
  ket_qua: 'THANH_CONG' | 'CHUA_CO_MAT_KHAU'
  so_dien_thoai: string
  token: string | null
  het_han_luc: string | null
  can_tao_ho_so: boolean
}

export interface LoginBody {
  so_dien_thoai: string
  mat_khau: string
}
