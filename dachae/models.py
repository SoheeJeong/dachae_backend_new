# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class TbArkworkInfo(models.Model):
    image_id = models.AutoField(primary_key=True)
    img_path = models.CharField(max_length=100)
    title = models.CharField(max_length=50, blank=True, null=True)
    author = models.CharField(max_length=50, blank=True, null=True)
    era = models.CharField(max_length=50, blank=True, null=True)
    style = models.CharField(max_length=50, blank=True, null=True)
    company = models.ForeignKey('TbCompanyInfo', models.DO_NOTHING, blank=True, null=True)
    price = models.PositiveIntegerField(blank=True, null=True)
    h1 = models.PositiveIntegerField(blank=True, null=True)
    s1 = models.PositiveIntegerField(blank=True, null=True)
    v1 = models.PositiveIntegerField(blank=True, null=True)
    h2 = models.PositiveIntegerField(blank=True, null=True)
    s2 = models.PositiveIntegerField(blank=True, null=True)
    v2 = models.PositiveIntegerField(blank=True, null=True)
    h3 = models.PositiveIntegerField(blank=True, null=True)
    s3 = models.PositiveIntegerField(blank=True, null=True)
    v3 = models.PositiveIntegerField(blank=True, null=True)
    label1_id = models.PositiveIntegerField(blank=True, null=True)
    label2_id = models.PositiveIntegerField(blank=True, null=True)
    label3_id = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TB_ARKWORK_INFO'


class TbCompanyInfo(models.Model):
    company_id = models.AutoField(primary_key=True)
    company_nm = models.CharField(max_length=45)
    start_date = models.DateTimeField(blank=True, null=True)
    termination_date = models.DateTimeField(blank=True, null=True)
    site_url = models.CharField(max_length=1000, blank=True, null=True)
    contract_type = models.CharField(max_length=45, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TB_COMPANY_INFO'


class TbLabelInfo(models.Model):
    label_id = models.PositiveIntegerField(primary_key=True)
    label_nm = models.CharField(max_length=50)
    label_freq = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TB_LABEL_INFO'


class TbPurchaseInfo(models.Model):
    purchase_id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=40, blank=True, null=True)
    image_id = models.PositiveIntegerField()
    server_time = models.DateTimeField(blank=True, null=True)
    company = models.ForeignKey(TbCompanyInfo, models.DO_NOTHING)
    price = models.CharField(max_length=45, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TB_PURCHASE_INFO'


class TbSampleList(models.Model):
    sample_id = models.AutoField(primary_key=True)
    sample_path = models.CharField(max_length=70)
    artwork = models.ForeignKey(TbArkworkInfo, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TB_SAMPLE_LIST'


class TbUploadInfo(models.Model):
    upload_id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=40)
    server_time = models.DateTimeField()
    room_img = models.CharField(max_length=1000)
    clustering_img = models.CharField(max_length=1000, blank=True, null=True)
    label1_id = models.IntegerField(blank=True, null=True)
    label2_id = models.IntegerField(blank=True, null=True)
    label3_id = models.IntegerField(blank=True, null=True)
    img_id = models.CharField(max_length=45, blank=True, null=True)
    like = models.CharField(max_length=45, blank=True, null=True)
    purchase_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TB_UPLOAD_INFO'


class TbUserInfo(models.Model):
    user_id = models.CharField(primary_key=True, max_length=50)
    social_platform = models.CharField(max_length=50, blank=True, null=True)
    user_nm = models.CharField(max_length=50)
    birthday_date = models.CharField(max_length=50, blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    gender = models.CharField(max_length=50, blank=True, null=True)
    age_range = models.CharField(max_length=50, blank=True, null=True)
    rgst_date = models.DateTimeField()
    level = models.CharField(max_length=50, blank=True, null=True)
    role = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TB_USER_INFO'


class TbUserLog(models.Model):
    session_id = models.AutoField(primary_key=True)
    page_id = models.PositiveIntegerField(blank=True, null=True)
    server_time = models.DateTimeField()
    user = models.ForeignKey(TbUserInfo, models.DO_NOTHING)
    connection_env = models.CharField(max_length=50)
    device_type = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'TB_USER_LOG'


class TbWishlistInfo(models.Model):
    wish_id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=40)
    image_id = models.PositiveIntegerField()
    server_time = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'TB_WISHLIST_INFO'


class AccountEmailaddress(models.Model):
    email = models.CharField(unique=True, max_length=254)
    verified = models.IntegerField()
    primary = models.IntegerField()
    user = models.ForeignKey('AuthUser', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'account_emailaddress'


class AccountEmailconfirmation(models.Model):
    created = models.DateTimeField()
    sent = models.DateTimeField(blank=True, null=True)
    key = models.CharField(unique=True, max_length=64)
    email_address = models.ForeignKey(AccountEmailaddress, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'account_emailconfirmation'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class DjangoSite(models.Model):
    domain = models.CharField(unique=True, max_length=100)
    name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'django_site'


class SocialaccountSocialaccount(models.Model):
    provider = models.CharField(max_length=30)
    uid = models.CharField(max_length=191)
    last_login = models.DateTimeField()
    date_joined = models.DateTimeField()
    extra_data = models.TextField()
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialaccount'
        unique_together = (('provider', 'uid'),)


class SocialaccountSocialapp(models.Model):
    provider = models.CharField(max_length=30)
    name = models.CharField(max_length=40)
    client_id = models.CharField(max_length=191)
    secret = models.CharField(max_length=191)
    key = models.CharField(max_length=191)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialapp'


class SocialaccountSocialappSites(models.Model):
    socialapp = models.ForeignKey(SocialaccountSocialapp, models.DO_NOTHING)
    site = models.ForeignKey(DjangoSite, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialapp_sites'
        unique_together = (('socialapp', 'site'),)


class SocialaccountSocialtoken(models.Model):
    token = models.TextField()
    token_secret = models.TextField()
    expires_at = models.DateTimeField(blank=True, null=True)
    account = models.ForeignKey(SocialaccountSocialaccount, models.DO_NOTHING)
    app = models.ForeignKey(SocialaccountSocialapp, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialtoken'
        unique_together = (('app', 'account'),)
