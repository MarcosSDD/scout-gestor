export type PaginatedMeta = {
  count: number;
  next: string | null;
  previous: string | null;
  page?: number;
  page_size?: number;
};

export type ApiSuccess<TData, TMeta = unknown> = {
  success: true;
  message: string;
  data: TData;
  meta?: TMeta;
};

export type ApiError = {
  success: false;
  error: {
    code: string;
    message: string;
    details: unknown;
    /** HTTP status when the error originated in an HTTP response. */
    status: number | null;
  };
};

export type DetailPermissions = {
  can_edit?: boolean;
  can_edit_identity?: boolean;
  can_edit_contact?: boolean;
  can_replace_photo?: boolean;
  can_download_photo?: boolean;
  can_download_certificate?: boolean;
  can_manage_progression?: boolean;
  can_edit_committee?: boolean;
  can_reassign_unit?: boolean;
  can_renew_certificate?: boolean;
  can_create_unit?: boolean;
  can_create_subgroup?: boolean;
  can_manage_memberships?: boolean;
  can_manage_adult_assignments?: boolean;
  can_assign_leader?: boolean;
  can_reassign?: boolean;
  can_edit_role?: boolean;
};

export type DetailMeta = {
  permissions?: DetailPermissions;
};
