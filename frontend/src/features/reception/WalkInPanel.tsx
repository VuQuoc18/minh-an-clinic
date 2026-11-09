import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Alert, AlertDescription, AlertTitle } from '../../components/ui/alert'
import { Button } from '../../components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '../../components/ui/card'
import {
  Field,
  FieldError,
  FieldHint,
  Fieldset,
} from '../../components/ui/field'
import { Input } from '../../components/ui/input'
import { Label, LabelRequired } from '../../components/ui/label'
import { NativeSelect } from '../../components/ui/native-select'
import { Radio, RadioGroup } from '../../components/ui/radio'
import { formatDate, formatTime } from '../../lib/format'
import { ApiError } from '../../lib/http'
import {
  createWalkIn,
  getWalkInSuggestions,
  listSpecialties,
  searchProfiles,
} from './api'
import { NewProfileForm } from './NewProfileForm'
import type { Appointment, NewProfile } from './types'

interface Props {
  onCreated: (appointment: Appointment) => void
  onCancel: () => void
}

const PHONE_RE = /^0[0-9]{9}$/

function errorMessage(error: unknown): string {
  return error instanceof ApiError
    ? error.message
    : 'Không thực hiện được. Vui lòng thử lại.'
}

/** Luồng khách vãng lai (FR-TD-02): chuyên khoa, khung trống, hồ sơ, tạo lịch đã đến. */
export function WalkInPanel({ onCreated, onCancel }: Props) {
  const queryClient = useQueryClient()
  const [specialtyId, setSpecialtyId] = useState<number | null>(null)
  const [slotId, setSlotId] = useState<number | null>(null)
  const [phone, setPhone] = useState('')
  const [searchedPhone, setSearchedPhone] = useState<string | null>(null)
  const [phoneError, setPhoneError] = useState<string | null>(null)
  const [profileId, setProfileId] = useState<number | null>(null)
  const [newProfile, setNewProfile] = useState<NewProfile | null>(null)
  const [useNew, setUseNew] = useState(false)

  const specialties = useQuery({
    queryKey: ['specialties'],
    queryFn: listSpecialties,
  })
  const suggestions = useQuery({
    queryKey: ['walk-in-suggestions', specialtyId],
    queryFn: () => getWalkInSuggestions(specialtyId as number),
    enabled: specialtyId !== null,
  })
  const profiles = useQuery({
    queryKey: ['profiles', searchedPhone],
    queryFn: () => searchProfiles(searchedPhone as string),
    enabled: searchedPhone !== null,
  })
  const create = useMutation({
    mutationFn: createWalkIn,
    onSuccess: (appointment) => {
      void queryClient.invalidateQueries({ queryKey: ['appointments'] })
      onCreated(appointment)
    },
    onError: () => {
      // Khung có thể vừa bị người khác đặt: tải lại gợi ý.
      void queryClient.invalidateQueries({ queryKey: ['walk-in-suggestions'] })
    },
  })

  const changeSpecialty = (value: string) => {
    setSpecialtyId(value ? Number(value) : null)
    setSlotId(null)
    create.reset()
  }

  const submitSearch = () => {
    if (!PHONE_RE.test(phone)) {
      setPhoneError('Số điện thoại gồm 10 chữ số và bắt đầu bằng 0.')
      return
    }
    setPhoneError(null)
    setProfileId(null)
    setUseNew(false)
    setNewProfile(null)
    setSearchedPhone(phone)
  }

  const profileReady = useNew ? newProfile !== null : profileId !== null
  const canSubmit = slotId !== null && profileReady && !create.isPending

  const submit = () => {
    if (slotId === null) return
    if (useNew && newProfile)
      create.mutate({ slot_id: slotId, new_profile: newProfile })
    else if (profileId !== null)
      create.mutate({ slot_id: slotId, profile_id: profileId })
  }

  const found = profiles.data ?? []
  const data = suggestions.data

  return (
    <Card asChild>
      <section aria-labelledby="walk-in-title">
        <CardHeader>
          <CardTitle id="walk-in-title">Khách vãng lai</CardTitle>
          <CardDescription>
            Chọn chuyên khoa, khung giờ trống sớm nhất và hồ sơ bệnh nhân.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <Field>
            <Label htmlFor="walk-in-specialty">
              Chuyên khoa <LabelRequired />
            </Label>
            <NativeSelect
              id="walk-in-specialty"
              value={specialtyId ?? ''}
              onChange={(event) => changeSpecialty(event.target.value)}
            >
              <option value="">Chọn chuyên khoa</option>
              {specialties.data?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </NativeSelect>
          </Field>

          {suggestions.isError && (
            <Alert variant="destructive" role="alert">
              <AlertTitle>Không tải được khung giờ trống</AlertTitle>
              <AlertDescription>
                {errorMessage(suggestions.error)}
              </AlertDescription>
            </Alert>
          )}

          {data && data.suggestions.length === 0 && (
            <Alert variant="warning" role="status">
              <AlertTitle>{data.message ?? 'Hết chỗ hôm nay'}</AlertTitle>
              {data.next_available_date ? (
                <AlertDescription>
                  Ngày gần nhất còn trống:{' '}
                  {formatDate(data.next_available_date)}.
                </AlertDescription>
              ) : (
                <AlertDescription>
                  Chưa có ngày nào còn trống trong 30 ngày tới.
                </AlertDescription>
              )}
            </Alert>
          )}

          {data && data.suggestions.length > 0 && (
            <Fieldset>
              <legend className="ds-label">
                Khung giờ trống sớm nhất của từng bác sĩ
              </legend>
              <RadioGroup>
                {data.suggestions.map((s) => (
                  <Radio
                    key={s.slot_id}
                    name="walk-in-slot"
                    checked={slotId === s.slot_id}
                    onChange={() => setSlotId(s.slot_id)}
                  >
                    {s.doctor_name} · {formatTime(s.start_time)} -{' '}
                    {formatTime(s.end_time)}
                    {s.is_walk_in_slot && ' (khung vãng lai)'}
                  </Radio>
                ))}
              </RadioGroup>
            </Fieldset>
          )}

          <Field>
            <Label htmlFor="walk-in-phone">
              Số điện thoại <LabelRequired />
            </Label>
            <div className="flex gap-2">
              <Input
                id="walk-in-phone"
                type="tel"
                inputMode="numeric"
                value={phone}
                aria-invalid={phoneError ? 'true' : undefined}
                aria-describedby={
                  phoneError ? 'walk-in-phone-error' : undefined
                }
                onChange={(event) => setPhone(event.target.value.trim())}
              />
              <Button variant="outline" onClick={submitSearch}>
                Tìm hồ sơ
              </Button>
            </div>
            {phoneError && (
              <FieldError id="walk-in-phone-error">{phoneError}</FieldError>
            )}
          </Field>

          {profiles.isError && (
            <Alert variant="destructive" role="alert">
              <AlertTitle>Không tìm được hồ sơ</AlertTitle>
              <AlertDescription>
                {errorMessage(profiles.error)}
              </AlertDescription>
            </Alert>
          )}

          {searchedPhone !== null && profiles.isSuccess && (
            <Fieldset>
              <legend className="ds-label">Hồ sơ bệnh nhân</legend>
              {found.length === 0 && (
                <FieldHint>
                  Chưa có hồ sơ với số điện thoại này. Nhập hồ sơ mới.
                </FieldHint>
              )}
              <RadioGroup>
                {found.map((p) => (
                  <Radio
                    key={p.id}
                    name="walk-in-profile"
                    checked={!useNew && profileId === p.id}
                    onChange={() => {
                      setUseNew(false)
                      setProfileId(p.id)
                    }}
                  >
                    {p.full_name} · {formatDate(p.birth_date)}
                    {p.is_primary && ' (hồ sơ chính)'}
                  </Radio>
                ))}
                <Radio
                  name="walk-in-profile"
                  checked={useNew}
                  onChange={() => {
                    setUseNew(true)
                    setProfileId(null)
                  }}
                >
                  Nhập hồ sơ mới
                </Radio>
              </RadioGroup>
            </Fieldset>
          )}

          {useNew && searchedPhone !== null && (
            <NewProfileForm
              initialPhone={searchedPhone}
              onChange={setNewProfile}
            />
          )}

          {create.isError && (
            <Alert variant="destructive" role="alert">
              <AlertTitle>Không tạo được lịch hẹn</AlertTitle>
              <AlertDescription>{errorMessage(create.error)}</AlertDescription>
            </Alert>
          )}
        </CardContent>
        <CardFooter className="flex justify-end gap-2">
          <Button variant="outline" onClick={onCancel}>
            Hủy
          </Button>
          <Button disabled={!canSubmit} onClick={submit}>
            Tạo lịch và xác nhận đến
          </Button>
        </CardFooter>
      </section>
    </Card>
  )
}
