import { render, screen } from '@testing-library/react'

import { AppProviders } from './providers'

describe('AppProviders', () => {
  it('renders child content', () => {
    render(
      <AppProviders>
        <div>Provider child</div>
      </AppProviders>,
    )

    expect(screen.getByText('Provider child')).toBeInTheDocument()
  })
})
