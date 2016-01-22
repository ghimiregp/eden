# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Template settings for CAP: Common Alerting Protocol
    """

    T = current.T

    settings.base.system_name = T("Sahana Alerting and Messaging Broker")
    settings.base.system_name_short = T("SAMBRO")

    # Pre-Populate
    settings.base.prepopulate += ("SAMBRO", "SAMBRO/Demo", "default/users")

    # Theme (folder to use for views/layout.html)
    #settings.base.theme = "SAMBRO"

    # The Registration functionality shouldn't be visible to the Public
    settings.security.registration_visible = False

    # Link Users to Organisations
    settings.auth.registration_requests_organisation = True

    # GeoNames username
    settings.gis.geonames_username = "eden_test"

    # checklist workflow
    settings.cap.ack_checklist = True

    # ack workflow
    settings.cap.ack_workflow = True

    # =========================================================================
    # System Settings
    # -------------------------------------------------------------------------
    # Security Policy
    # http://eden.sahanafoundation.org/wiki/S3/S3AAA#System-widePolicy
    # 1: Simple (default): Global as Reader, Authenticated as Editor
    # 2: Editor role required for Update/Delete, unless record owned by session
    # 3: Apply Controller ACLs
    # 4: Apply both Controller & Function ACLs
    # 5: Apply Controller, Function & Table ACLs
    # 6: Apply Controller, Function, Table ACLs and Entity Realm
    # 7: Apply Controller, Function, Table ACLs and Entity Realm + Hierarchy
    # 8: Apply Controller, Function, Table ACLs, Entity Realm + Hierarchy and Delegations
    settings.security.policy = 4 # Controller-Function ACLs

    # Record Approval
    settings.auth.record_approval = True
    # cap_alert record requires approval before sending
    settings.auth.record_approval_required_for = ("cap_alert",)
    # Don't auto-approve so that can save draft
    settings.auth.record_approval_manual = ("cap_alert",)

    # =========================================================================
    # Module Settings
    # -------------------------------------------------------------------------
    # CAP Settings
    # Uncomment this according to country profile
    #settings.cap.restrict_fields = True

    # -------------------------------------------------------------------------
    # Notifications

    # Template for the subject line in update notifications
    settings.msg.notify_subject = "$S %s" % T("Alert Notification")

    # Filename for FTP
    # Characters not allowed are [\ / : * ? " < > | % .]
    # https://en.wikipedia.org/wiki/Filename
    # http://docs.attachmate.com/reflection/ftp/15.6/guide/en/index.htm?toc.htm?6503.htm
    settings.sync.upload_filename = "$s-%s" % ("recent_alert")
    
    # Whether to tweet alerts
    settings.cap.post_to_twitter = True

    # -------------------------------------------------------------------------
    # L10n (Localization) settings
    languages = OrderedDict([
        #("ar", "العربية"),
        ("dv", "ދިވެހި"), # Divehi (Maldives)
        ("en-US", "English"),
        #("es", "Español"),
        #("fr", "Français"),
        #("km", "ភាសាខ្មែរ"),        # Khmer
        #("mn", "Монгол хэл"),  # Mongolian
        ("my", "မြန်မာစာ"),        # Burmese
        #("ne", "नेपाली"),          # Nepali
        #("prs", "دری"),        # Dari
        #("ps", "پښتو"),        # Pashto
        #("tet", "Tetum"),
        #("th", "ภาษาไทย"),        # Thai
        ("tl", "Tagalog"), # Filipino
        #("vi", "Tiếng Việt"),   # Vietnamese
        #("zh-cn", "中文 (简体)"),
    ])
    settings.L10n.languages = languages
    settings.cap.languages = languages
    # Translate the cap_area name
    settings.L10n.translate_cap_area = True

    # -------------------------------------------------------------------------
    # Messaging
    # Parser
    settings.msg.parser = "SAMBRO"

    # -------------------------------------------------------------------------
    # Organisations
    # Enable the use of Organisation Branches
    settings.org.branches = True
    # Show branches as tree rather than as table
    settings.org.branches_tree_view = True

    # -------------------------------------------------------------------------
    def customise_msg_rss_channel_resource(r, tablename):

        # @ToDo: We won't be able to automate this as we have 2 sorts, so will need the user to select manually
        # Can we add a component for the parser for S3CSV imports?

        # UX: separate menu items distinguished via get_var
        # @ToDo: Add menu entries for "Create RSS Feed for CAP" & "Create RSS Feed for CMS"
        type = current.request.get_vars.get("type", None)
        if type == "cap":
            fn = "parse_rss_2_cap"
        else:
            fn = "parse_rss_2_cms"

        s3db = current.s3db
        def onaccept(form):
            # Normal onaccept
            s3db.msg_channel_onaccept(form)
            _id = form.vars.id
            db = current.db
            table = db.msg_rss_channel
            channel_id = db(table.id == _id).select(table.channel_id,
                                                    limitby=(0, 1)).first().channel_id
            # Link to Parser
            table = s3db.msg_parser
            _id = table.insert(channel_id=channel_id, function_name=fn, enabled=True)
            s3db.msg_parser_enable(_id)

            async = current.s3task.async
            # Poll
            async("msg_poll", args=["msg_rss_channel", channel_id])

            # Parse
            async("msg_parse", args=[channel_id, fn])

        s3db.configure(tablename,
                       create_onaccept = onaccept,
                       )

    settings.customise_msg_rss_channel_resource = customise_msg_rss_channel_resource

    # -------------------------------------------------------------------------
    def customise_msg_twitter_channel_resource(r, tablename):

        s3db = current.s3db
        def onaccept(form):
            # Normal onaccept
            s3db.msg_channel_onaccept(form)
            _id = form.vars.id
            db = current.db
            table = db.msg_twitter_channel
            channel_id = db(table.id == _id).select(table.channel_id,
                                                    limitby=(0, 1)).first().channel_id
            # Link to Parser
            table = s3db.msg_parser
            _id = table.insert(channel_id=channel_id, function_name="parse_tweet", enabled=True)
            s3db.msg_parser_enable(_id)

            async = current.s3task.async
            # Poll
            async("msg_poll", args=["msg_twitter_channel", channel_id])

            # Parse
            async("msg_parse", args=[channel_id, "parse_tweet"])

        s3db.configure(tablename,
                       create_onaccept = onaccept,
                       )

    settings.customise_msg_twitter_channel_resource = customise_msg_twitter_channel_resource

    # -------------------------------------------------------------------------
    def customise_org_organisation_resource(r, tablename):

        from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink
        crud_form = S3SQLCustomForm("name",
                                    "acronym",
                                    S3SQLInlineLink("organisation_type",
                                                    field = "organisation_type_id",
                                                    label = T("Type"),
                                                    multiple = False,
                                                    #widget = "hierarchy",
                                                    ),
                                    S3SQLInlineComponent(
                                        "tag",
                                        label = T("CAP OID"),
                                        multiple = False,
                                        fields = [("", "value")],
                                        filterby = dict(field = "tag",
                                                        options = "cap_oid",
                                                        ),
                                        ),
                                    "website",
                                    "comments",
                                    )

        current.s3db.configure("org_organisation",
                               crud_form = crud_form,
                               )

    settings.customise_org_organisation_resource = customise_org_organisation_resource

    # -------------------------------------------------------------------------
    def customise_cap_alert_resource(r, tablename):

        db = current.db
        s3db = current.s3db
        def onapprove(record):
            # Normal onapprove
            s3db.cap_alert_approve(record)

            # Sync FTP Repository
            current.s3task.async("cap_ftp_sync")
            
            if settings.get_cap_checklist() or settings.get_cap_ack():
                alert_id = int(record["id"])
                itable = s3db.cap_info
                ltable = s3db.cap_area_location
                
                all_info = []

                # Event Type should be the same for all Info segments in the same alert
                info_row = db(itable.alert_id == alert_id).select(\
                                                    itable.event_type_id,
                                                    itable.priority,
                                                    limitby=(0, 1)).first()
                area_location_rows = db(ltable.alert_id == alert_id).select(\
                                                        ltable.location_id)
                if info_row and area_location_rows:
                    ptable = s3db.pr_group
                    stable = s3db.pr_subscription
                    ftable = s3db.pr_filter

                    # Hard-coded group_type; 3 is relief team
                    query = (ptable.deleted != True) & \
                            (stable.deleted != True) & \
                            (ptable.group_type == 3) & \
                            (stable.pe_id == ptable.pe_id) & \
                            (ftable.id == stable.filter_id)
                    rows = db(query).select(ptable.id,
                                            stable.id,
                                            ftable.query)
                    if rows:
                        alert_locations = [area_location_row.location_id
                                           for area_location_row in area_location_rows]

                        for row in rows:
                            event_types, priorities, locations = get_events_priorities_locations(\
                                                                    row.pr_filter.query)
                            check, location_info = get_info(info_row.event_type_id,
                                                            info_row.priority,
                                                            alert_locations,
                                                            event_types,
                                                            priorities,
                                                            locations,
                                                            )
                            if check:
                                checklist_ids = []
                                ack_ids = []
                                if settings.get_cap_checklist():
                                    checklist_ids = create_checklist_from_template(\
                                                        row.pr_subscription.id,
                                                        info_row.event_type_id,
                                                        row.pr_group.id, # group_id
                                                        location_info,
                                                        )

                                if settings.get_cap_ack():
                                    ack_ids = create_ack(alert_id, location_info)

                                for checklist_id in checklist_ids:
                                    mapping = {alert_id:
                                               [{checklist_id["pe_id"]:
                                                 [{checklist_id["location_id"]:
                                                   [{ack_id[checklist_id["location_id"]]: checklist_id["checklist_id"]}]
                                                   }]
                                                 }]
                                               }
                                    all_info.append(mapping)

            # Twitter Post
            if settings.get_cap_post_to_twitter():
                try:
                    import tweepy
                except ImportError:
                    current.log.debug("tweepy module needed for sending tweets")
                else:
                    T = current.T
                    db = current.db
                    alert_id = int(record["id"])
                    atable = s3db.cap_alert
                    itable = s3db.cap_info
        
                    arow = db(atable.id == alert_id).select(atable.status,
                                                            atable.sender,
                                                            atable.sent,
                                                            limitby=(0, 1)).first()
                    # Using English Info Segment for now
                    # Because tweet has Info Headline
                    iquery = (itable.alert_id == alert_id) & \
                             (itable.language == "en-US")
                    irow = db(iquery).select(itable.headline,
                                             itable.web,
                                             limitby=(0, 1)).first()
                    # @ToDo: shorten url
                    # @ToDo: Handle the multi-message nicely?
                    # @ToDo: Send resource url with tweet
                    twitter_text = \
("""%(Status)s: %(Headline)s
%(SENDER)s: %(SenderName)s
%(WEBSITE)s: %(Website)s""") % dict(Status = arow.status,
                                    Headline = irow.headline,
                                    SENDER = T("Sender"),
                                    SenderName = arow.sender,
                                    WEBSITE = T("Website"),
                                    Website = irow.web)
                    try:
                        current.msg.send_tweet(text=twitter_text)
                    except tweepy.error.TweepError, e:
                        current.log.debug("Sending tweets failed: %s" % e)

        s3db.configure(tablename,
                       onapprove = onapprove,
                       )

    settings.customise_cap_alert_resource = customise_cap_alert_resource

    # -------------------------------------------------------------------------
    def get_events_priorities_locations(filter):
        """
            Get the event types, priorities and locations associated with the filter
        """

        event_types = []
        priorities = []
        locations = []

        filters_ = json.loads(filters)
        filters_ = [filter_ for filter_ in filters_ if filter_[1] is not None]
        if len(filters_) > 0:
            from s3 import s3_str
            L0 = None
            L1 = None
            L2 = None
            L3 = None
            L4 = None
            L5 = None
            for filter_ in filters_:
                # Get the prefix
                prefix = s3_str(filter_[0]).strip("[]")
                # Get the value for prefix
                values = filter_[1].split(",")
                if prefix == "event_type_id__belongs":
                    event_types = [int(s3_str(value)) for value in values]
                elif prefix == "priority__belongs":
                    priorities = [int(s3_str(value)) for value in values]
                elif prefix == "location_id$L0__belongs":
                    L0 = [s3_str(value) for value in values]
                elif prefix == "location_id$L1__belongs":
                    L1 = [s3_str(value) for value in values]
                elif prefix == "location_id$L2__belongs":
                    L2 = [s3_str(value) for value in values]
                elif prefix == "location_id$L3__belongs":
                    L3 = [s3_str(value) for value in values]
                elif prefix == "location_id$L4__belongs":
                    L4 = [s3_str(value) for value in values]
                elif prefix == "location_id$L5__belongs":
                    L5 = [s3_str(value) for value in values]
            if L0 is not None:
                ltable = s3db.gis_location
                locations_l1 = []
                locations_l2 = []

                query_l0 = (ltable.level == "L0") & \
                           (ltable.name.belongs(L0))
                rows_l0 = db(query_l0).select(ltable.id)
                locations = locations_l0 = [row_l0.id for row_l0 in rows_l0]

                if L1 is not None:
                    query_l1 = (ltable.name.belongs(L1)) & \
                               (ltable.level == "L1") & \
                               (ltable.parent.belongs(locations_l0))
                    rows_l1 = db(query_l1).select(ltable.id)
                    locations = locations_l1 = [row_l1.id for row_l1 in rows_l1]

                if L2 is not None:
                    query_l2 = (ltable.name.belongs(L2)) & \
                               (ltable.level == "L2") & \
                               (ltable.parent.belongs(locations_l0) | \
                                ltable.parent.belongs(locations_l1))
                    rows_l2 = db(query_l2).select(ltable.id)
                    locations = locations_l2 = [row_l2.id for row_l2 in rows_l2]

                if L3 is not None:
                    query_l3 = (ltable.name.belongs(L3)) & \
                               (ltable.level == "L3") & \
                               (ltable.parent.belongs(locations_l1) | \
                                ltable.parent.belongs(location_l2))
                    rows_l3 = db(query_l3).select(ltable.id)
                    locations = [row_l3.id for row_l3 in rows_l3]
                    if L4 is not None:
                        query_l4 = (ltable.name.belongs(L4)) & \
                                   (ltable.level == "L4") & \
                                   (ltable.parent.belongs(locations))
                        rows_l4 = db(query_l4).select(ltable.id)
                        locations = [row_l4.id for row_l4 in rows_l4]
                        if L5 is not None:
                            query_l5 = (ltable.name.belongs(L5)) & \
                                       (ltable.level == "L5") & \
                                       (ltable.parent.belongs(locations))
                            rows_l5 = db(query_l5).select(ltable.id)
                            locations = [row_l5.id for row_l5 in rows_l5]

        return (event_types, priorities, locations)

    # -------------------------------------------------------------------------
    def get_info(alert_event_type,
                 alert_priority,
                 alert_locations,
                 event_types,
                 priorities,
                 locations
                 ):
        """
            Check whether filter has the alert event_type and priority
            check the intersection of the subscription with the alert locations
            Return True and location_ids of subscription that intersect with the
            alert locations, False and empty list if otherwise.
        """

        intersects = current.gis.intersects
        check_event = True
        check_priority = True
        check_location = False
        location_info = []

        if len(event_types) > 0:
            # Filter
            if not (alert_event_type in event_types):
                check_event = False
        if len(priorities) > 0:
            # Filter
            if not (alert_priority in priorities):
                check_priority = False
        if len(locations) > 0:
            # If location filter applies
            for alert_location in alert_locations:
                for location_id in locations:                
                    if intersects(location_id, alert_location):
                        check_location = True
                        # NB: if len(location_info) > 1 for same alert_location => cross boundary?
                        location_info.append({"subscription_location_id": location_id,
                                              "alert_location": alert_location})
        else:
            # Else subscribed for all locations
            check_location = True

        return (check_event and check_priority and check_location, location_info)

    # -------------------------------------------------------------------------
    def create_checklist_from_template(alert_event_type,
                                       group_id,
                                       location_info
                                       ):
        """
            Create a specific checklist from a template
            @param alert_event_id: The event_type_id for a particular alert ID
            @param group_id: The pr_group ID to send the checklist
            @param location_info: Dictionary of the intersection between 
            alert location and subscription location
        """

        tfieldnames = ("name",
                       "instruction",
                       )
        tefieldnames = ("name",
                        "checklist_order",
                       )

        db = current.db
        s3db = current.s3db
        gtable = s3db.pr_group_membership
        ptable = s3db.pr_person
        checklist_ids = []
        
        query = (gtable.deleted != True) & \
                (gtable.group_id == group_id) & \
                (gtable.person_id == ptable.id)
        prows = db(query).select(ptable.pe_id)
        if prows:
            template_table = s3db.event_checklist_template
            template_entries_table = s3db.event_checklist_template_entry
            checklist_table = s3db.event_checklist
            entries_table = s3db.event_checklist_entry

            s3_set_record_owner = current.auth.s3_set_record_owner
            #onaccept = s3db.onaccept
            cinsert = checklist_table.insert
            einsert = entries_table.insert

            pe_ids = [row.pr_person.pe_id for row in prows]

            query = (template_table.event_type_id == alert_event_type) & \
                    (template_table.deleted != True)
            for info in location_info:
                # NB if len(location_info) > 1 for same alert_location=> Alert share more than one boundary                
                query_ = query & (template_table.location_id == info["subscription_location_id"] or None)
                template_rows = db(query_).select(template_table.id,
                                                  template_table.location_id,
                                                  limitby=(0, 2))
                if len(template_rows) < 1:
                    return checklist_ids
                elif len(template_rows) > 1:
                    # Remove the Location Default
                    _filter = lambda row: row.location_id == None
                    template_rows.exclude(_filter)
                
                template_row = template_rows.first()

                template = db(template_table.id == template_row.id).select(\
                                                        *tfieldnames,
                                                        limitby=(0, 1)).first()
                tequery = (template_entries_table.checklist_template_id == template_row.id) & \
                          (template_entries_table.deleted != True)
                template_entries = db(tequery).select(*tefieldnames)

                for pe_id in pe_ids:
                    cdata = {"pe_id": pe_ids[pe_id],
                             "location_id": info["alert_location"],
                             }
                    for field in tfieldnames:
                        cdata[field] = template[field]
    
                    cid = cinsert(**cdata)
                    s3_set_record_owner(checklist_table, cid)
                    # Uncomment this when there is onaccept hook in event_checklist table
                    #onaccept(checklist_table, dict(id=cid))
    
                    prop = {"pe_id": pe_ids[pe_id],
                            "checklist_id": cid,
                            "alert_location": info["alert_location"],
                            "location_id" : info["subscription_location_id"]
                            }
                    checklist_ids.append(prop)
    
                    if template_entries:
                        # Add checklist template entries
                        for row in template_entries:
                            edata = {"event_checklist_id": cid,
                                     }
                            for field in tefieldnames:
                                edata[field] = row[field]
                            eid = einsert(**edata)
                            s3_set_record_owner(entries_table, eid)
                            # Uncomment this when there is onaccept hook in event_checklist table
                            #onaccept(entires_table, dict(id=eid))

        return checklist_ids

    # -------------------------------------------------------------------------
    def create_ack(alert_id, location_info):
        """
            Create a specific acknowledgement
            @param alert_id: The particular alert ID for acknowledging
            @param location_info: Dictionary of the intersection between 
            alert location and subscription location
        """

        ack_table = current.s3db.cap_alert_ack
        ack_ids = []
        for info in  location_info:        
            ack_id = ack_table.insert(alert_id = alert_id,
                                      location_id = info["alert_location"])
            current.auth.s3_set_record_owner(ack_table, ack_id)
            # Uncomment this when there is onaccept hook
            #current.s3db.onaccept(ack_table, dict(id=ack_id))
            ack_ids.append({info["subscription_location_id"]: ack_id})
        return ack_ids
        
    # -------------------------------------------------------------------------
    def customise_sync_repository_controller(**attr):

        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True

            if r.representation == "popup":
                table = r.table
                table.apitype.default = "ftp"
                table.apitype.readable = table.apitype.writable = False
                table.accept_push.readable = table.accept_push.writable = False
                table.synchronise_uuids.readable = \
                                        table.synchronise_uuids.writable = False
                table.uuid.readable = table.uuid.writable = False

            return result
        s3.prep = custom_prep

        return attr

    settings.customise_sync_repository_controller = customise_sync_repository_controller

    # -------------------------------------------------------------------------
    def customise_pr_subscription_controller(**attr):

        from gluon.html import URL, A
        from s3 import S3CRUD
        s3 = current.response.s3
        auth = current.auth
        has_role = auth.s3_has_role
        # Filter admin based subscription based on roles
        if not (has_role("ALERT_EDITOR") or \
                has_role("ALERT_APPROVER")):
            s3.filter = (current.s3db.pr_subscription.owned_by_user == auth.user.id)
        else:
            s3.filter = (current.s3db.pr_subscription.owned_by_group != None)
        # Custom postp
        standard_postp = s3.postp
        def custom_postp(r, output):
            # Call standard postp
            if callable(standard_postp):
                output = standard_postp(r, output)

            if r.interactive and isinstance(output, dict):
                # Modify Open Button
                url = URL(c="default", f="index", args=["subscriptions"],
                          vars={"subscription_id": "[id]"})
                if not (has_role("ALERT_EDITOR") or \
                        has_role("ALERT_APPROVER")):
                    S3CRUD.action_buttons(r, read_url=url)
                else:
                    S3CRUD.action_buttons(r, update_url=url)
                # Modify Add Button
                if "form" in output:
                    add_btn = A(T("Create Subscription"),
                                _class="action-btn",
                                _href=URL(c="default", f="index", args=["subscriptions"])
                                )
                    output["showadd_btn"] = add_btn

            return output
        s3.postp = custom_postp

        return attr

    settings.customise_pr_subscription_controller = customise_pr_subscription_controller

    # -------------------------------------------------------------------------
    def customise_cap_warning_priority_resource(r, tablename):

        s3db = current.s3db
        def onaccept(form):
            # Normal onaccept if any
            form_vars = form.vars
            color_code = form_vars.color_code
            if color_code:
                db = current.db
                stable = s3db.gis_style
                etable = s3db.gis_layer_entity
                rows = db(etable.instance_type == "gis_layer_feature"). \
                                                        select(etable.layer_id)
                query = (stable.layer_id.belongs([row.layer_id for row in rows]))
                rows = db(query).select(stable.id, stable.style)
                if rows:
                    from s3 import IS_JSONS3
                    name = form_vars.name
                    for row in rows:
                        style = row.style
                        if style:
                            if isinstance(style, basestring):
                                style = json.loads(style)
                            sdata = dict(prop = "priority",
                                         fill = color_code,
                                         fillOpacity = 0.4,
                                         cat = name,
                                         )
                            if sdata not in style:
                                style.append(sdata)
                                style = IS_JSONS3()(json.dumps(style))[0]
                                db(stable.id == row.id).update(style = style)

        s3db.configure(tablename,
                       create_onaccept = onaccept,
                       )

    settings.customise_cap_warning_priority_resource = customise_cap_warning_priority_resource

    # -------------------------------------------------------------------------
    # Comment/uncomment modules here to disable/enable them
    # @ToDo: Have the system automatically enable migrate if a module is enabled
    # Modules menu is defined in modules/eden/menu.py
    settings.modules = OrderedDict([
        # Core modules which shouldn't be disabled
        ("default", Storage(
            name_nice = T("Home"),
            restricted = False, # Use ACLs to control access to this module
            access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
            module_type = None  # This item is not shown in the menu
        )),
        ("admin", Storage(
            name_nice = T("Administration"),
            #description = "Site Administration",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
        ("appadmin", Storage(
            name_nice = T("Administration"),
            #description = "Site Administration",
            restricted = True,
            module_type = None  # No Menu
        )),
        ("errors", Storage(
            name_nice = T("Ticket Viewer"),
            #description = "Needed for Breadcrumbs",
            restricted = False,
            module_type = None  # No Menu
        )),
        ("sync", Storage(
            name_nice = T("Synchronization"),
            #description = "Synchronization",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
        #("tour", Storage(
        #    name_nice = T("Guided Tour Functionality"),
        #    module_type = None,
        #)),
        ("translate", Storage(
            name_nice = T("Translation Functionality"),
            #description = "Selective translation of strings based on module.",
            module_type = None,
        )),
        ("gis", Storage(
            name_nice = T("Mapping"),
            #description = "Situation Awareness & Geospatial Analysis",
            restricted = True,
            module_type = 6,     # 6th item in the menu
        )),
        ("pr", Storage(
            name_nice = T("Person Registry"),
            #description = "Central point to record details on People",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = 10
        )),
        ("org", Storage(
            name_nice = T("Organizations"),
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            restricted = True,
            module_type = 10
        )),
        # All modules below here should be possible to disable safely
        #("hrm", Storage(
        #    name_nice = T("Staff"),
        #    #description = "Human Resources Management",
        #    restricted = True,
        #    module_type = 2,
        #)),
        ("cap", Storage(
            name_nice = T("Alerting"),
            #description = "Create & broadcast CAP alerts",
            restricted = True,
            module_type = 1,
        )),
        ("cms", Storage(
          name_nice = T("Content Management"),
          #description = "Content Management System",
          restricted = True,
          module_type = 10,
        )),
        ("doc", Storage(
            name_nice = T("Documents"),
            #description = "A library of digital resources, such as photos, documents and reports",
            restricted = True,
            module_type = 10,
        )),
        ("msg", Storage(
            name_nice = T("Messaging"),
            #description = "Sends & Receives Alerts via Email & SMS",
            restricted = True,
            # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
            module_type = None,
        )),
        ("event", Storage(
            name_nice = T("Events"),
            #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
            restricted = True,
            module_type = 10,
        )),
    ])

# END =========================================================================
