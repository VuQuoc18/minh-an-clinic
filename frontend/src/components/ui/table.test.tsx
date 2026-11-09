import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import {
  Table,
  TableBody,
  TableCell,
  TableCellActions,
  TableCellNum,
  TableHead,
  TableHeader,
  TableRow,
} from './table'

function renderTable() {
  return render(
    <Table aria-label="Bảng thử">
      <TableHeader>
        <TableRow>
          <TableHead>Tên</TableHead>
          <TableHead scope="row">Hàng</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell>A</TableCell>
          <TableCellNum>12</TableCellNum>
          <TableCellActions>Xóa</TableCellActions>
        </TableRow>
      </TableBody>
    </Table>,
  )
}

describe('Table', () => {
  it('bọc bảng trong ds-table-container và áp ds-table', () => {
    const { container } = renderTable()
    expect(container.firstElementChild).toHaveClass('ds-table-container')
    expect(screen.getByRole('table', { name: 'Bảng thử' })).toHaveClass(
      'ds-table',
    )
  })

  it('TableHead mặc định scope=col và cho ghi đè', () => {
    renderTable()
    expect(screen.getByRole('columnheader', { name: 'Tên' })).toHaveAttribute(
      'scope',
      'col',
    )
    expect(screen.getByText('Hàng')).toHaveAttribute('scope', 'row')
  })

  it('ô số và ô thao tác có class riêng', () => {
    renderTable()
    expect(screen.getByText('12')).toHaveClass('ds-table-num')
    expect(screen.getByText('Xóa')).toHaveClass('ds-table-actions')
    expect(screen.getByText('A').className).toBe('')
  })
})
