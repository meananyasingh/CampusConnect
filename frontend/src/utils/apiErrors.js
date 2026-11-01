export function getApiErrorMessage(error) {
  const data = error.response?.data
  if (!data) return 'Unable to reach the server. Please try again.'
  if (typeof data === 'string') return data
  if (data.detail) return data.detail
  if (data.non_field_errors?.length) return data.non_field_errors[0]

  const firstFieldError = Object.values(data).flat()[0]
  return firstFieldError || 'Please check the form and try again.'
}
